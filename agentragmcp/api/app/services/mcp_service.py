import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod

import httpx
from pydantic import BaseModel

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, get_logger_with_context
from agentragmcp.core.exceptions import (
    MCPError, 
    MCPServerNotFoundError, 
    MCPConnectionError
)

@dataclass
class MCPMessage:
    """Mensaje del protocolo MCP"""
    id: str
    method: str
    params: Dict[str, Any]
    jsonrpc: str = "2.0"

@dataclass
class MCPResponse:
    """Respuesta del protocolo MCP"""
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"

class MCPTool(BaseModel):
    """Definición de una herramienta MCP"""
    name: str
    description: str
    parameters: Dict[str, Any]
    server: str

class BaseMCPClient(ABC):
    """Cliente base abstracto para protocolo MCP"""
    
    def __init__(self, server_name: str, server_url: str):
        self.server_name = server_name
        self.server_url = server_url
        self.is_connected = False
        self.available_tools = {}
    
    @abstractmethod
    async def connect(self) -> bool:
        """Conecta al servidor MCP"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Desconecta del servidor MCP"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """Lista las herramientas disponibles"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta una herramienta"""
        pass

class HTTPMCPClient(BaseMCPClient):
    """Cliente MCP sobre HTTP"""
    
    def __init__(self, server_name: str, server_url: str, timeout: int = 30):
        super().__init__(server_name, server_url)
        self.timeout = timeout
        self.client = None
        self.session_id = None
    
    async def connect(self) -> bool:
        """Conecta al servidor MCP vía HTTP"""
        try:
            self.client = httpx.AsyncClient(timeout=self.timeout)
            
            # Inicializar sesión
            init_message = MCPMessage(
                id="init",
                method="initialize",
                params={
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "chatplants",
                        "version": "2.0.0"
                    }
                }
            )
            
            response = await self.client.post(
                f"{self.server_url}/mcp",
                json=init_message.__dict__
            )
            
            if response.status_code == 200:
                result = response.json()
                self.session_id = result.get("result", {}).get("sessionId")
                self.is_connected = True
                logger.info(f"Conectado a servidor MCP: {self.server_name}")
                
                # Cargar herramientas disponibles
                await self._load_available_tools()
                
                return True
            else:
                logger.error(f"Error conectando a {self.server_name}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error conectando a servidor MCP {self.server_name}: {e}")
            raise MCPConnectionError(self.server_name, self.server_url)
    
    async def disconnect(self):
        """Desconecta del servidor MCP"""
        if self.client:
            await self.client.aclose()
            self.is_connected = False
            logger.info(f"Desconectado de servidor MCP: {self.server_name}")
    
    async def _load_available_tools(self):
        """Carga las herramientas disponibles del servidor"""
        try:
            tools = await self.list_tools()
            self.available_tools = {tool.name: tool for tool in tools}
            logger.info(f"Cargadas {len(tools)} herramientas de {self.server_name}")
        except Exception as e:
            logger.warning(f"No se pudieron cargar herramientas de {self.server_name}: {e}")
    
    async def list_tools(self) -> List[MCPTool]:
        """Lista las herramientas disponibles"""
        if not self.is_connected:
            raise MCPError("Cliente no conectado")
        
        try:
            message = MCPMessage(
                id="list_tools",
                method="tools/list",
                params={}
            )
            
            response = await self.client.post(
                f"{self.server_url}/mcp",
                json=message.__dict__
            )
            
            if response.status_code == 200:
                result = response.json()
                tools_data = result.get("result", {}).get("tools", [])
                
                return [
                    MCPTool(
                        name=tool["name"],
                        description=tool["description"],
                        parameters=tool.get("inputSchema", {}),
                        server=self.server_name
                    )
                    for tool in tools_data
                ]
            else:
                raise MCPError(f"Error listando herramientas: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error listando herramientas de {self.server_name}: {e}")
            raise
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Ejecuta una herramienta"""
        if not self.is_connected:
            raise MCPError("Cliente no conectado")
        
        if tool_name not in self.available_tools:
            raise MCPError(f"Herramienta '{tool_name}' no disponible en {self.server_name}")
        
        try:
            message = MCPMessage(
                id=f"call_{tool_name}",
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": kwargs
                }
            )
            
            response = await self.client.post(
                f"{self.server_url}/mcp",
                json=message.__dict__
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {})
            else:
                raise MCPError(f"Error ejecutando herramienta: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error ejecutando herramienta {tool_name}: {e}")
            raise

class MCPService:
    """Servicio principal para gestión de MCP"""
    
    def __init__(self):
        self.settings = get_settings()
        self.clients: Dict[str, BaseMCPClient] = {}
        self.is_enabled = self.settings.MCP_ENABLED
        
        if self.is_enabled:
            logger.info("Inicializando servicio MCP")
            self._initialize_clients()
        else:
            logger.info("Servicio MCP deshabilitado")
    
    def _initialize_clients(self):
        """Inicializa los clientes MCP configurados"""
        for server_name, server_url in self.settings.MCP_SERVERS.items():
            try:
                # Por ahora solo HTTP, pero se puede extender para WebSocket, etc.
                client = HTTPMCPClient(server_name, server_url)
                self.clients[server_name] = client
                logger.info(f"Cliente MCP configurado: {server_name} -> {server_url}")
            except Exception as e:
                logger.error(f"Error configurando cliente MCP {server_name}: {e}")
    
    async def start(self):
        """Inicia todos los clientes MCP"""
        if not self.is_enabled:
            return
        
        connection_tasks = []
        for server_name, client in self.clients.items():
            task = asyncio.create_task(
                self._connect_client(server_name, client)
            )
            connection_tasks.append(task)
        
        if connection_tasks:
            results = await asyncio.gather(*connection_tasks, return_exceptions=True)
            
            successful_connections = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    server_name = list(self.clients.keys())[i]
                    logger.error(f"Error conectando a {server_name}: {result}")
                elif result:
                    successful_connections += 1
            
            logger.info(f"MCP Service iniciado: {successful_connections}/{len(self.clients)} conexiones exitosas")
    
    async def _connect_client(self, server_name: str, client: BaseMCPClient) -> bool:
        """Conecta un cliente específico"""
        try:
            return await client.connect()
        except Exception as e:
            logger.error(f"Error conectando cliente {server_name}: {e}")
            return False
    
    async def stop(self):
        """Detiene todos los clientes MCP"""
        if not self.is_enabled:
            return
        
        disconnect_tasks = []
        for client in self.clients.values():
            if client.is_connected:
                task = asyncio.create_task(client.disconnect())
                disconnect_tasks.append(task)
        
        if disconnect_tasks:
            await asyncio.gather(*disconnect_tasks, return_exceptions=True)
        
        logger.info("Servicio MCP detenido")
    
    def get_available_tools(self) -> List[MCPTool]:
        """Obtiene todas las herramientas disponibles de todos los servidores"""
        if not self.is_enabled:
            return []
        
        all_tools = []
        for client in self.clients.values():
            if client.is_connected:
                all_tools.extend(client.available_tools.values())
        
        return all_tools
    
    async def call_tool(
        self, 
        tool_name: str, 
        server_name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Ejecuta una herramienta MCP
        
        Args:
            tool_name: Nombre de la herramienta
            server_name: Servidor específico (opcional)
            **kwargs: Argumentos para la herramienta
        """
        if not self.is_enabled:
            raise MCPError("Servicio MCP deshabilitado")
        
        # Si se especifica servidor, usarlo directamente
        if server_name:
            if server_name not in self.clients:
                raise MCPServerNotFoundError(server_name)
            
            client = self.clients[server_name]
            if not client.is_connected:
                raise MCPConnectionError(server_name, client.server_url)
            
            return await client.call_tool(tool_name, **kwargs)
        
        # Buscar la herramienta en todos los servidores conectados
        for client in self.clients.values():
            if client.is_connected and tool_name in client.available_tools:
                return await client.call_tool(tool_name, **kwargs)
        
        raise MCPError(f"Herramienta '{tool_name}' no encontrada en ningún servidor")
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio MCP"""
        if not self.is_enabled:
            return {
                "status": "disabled",
                "enabled": False
            }
        
        connected_clients = sum(1 for client in self.clients.values() if client.is_connected)
        total_tools = len(self.get_available_tools())
        
        client_status = {}
        for name, client in self.clients.items():
            client_status[name] = {
                "connected": client.is_connected,
                "url": client.server_url,
                "tools": len(client.available_tools)
            }
        
        return {
            "status": "healthy" if connected_clients > 0 else "degraded",
            "enabled": True,
            "total_servers": len(self.clients),
            "connected_servers": connected_clients,
            "total_tools": total_tools,
            "servers": client_status
        }
    
    def is_tool_available(self, tool_name: str) -> bool:
        """Verifica si una herramienta está disponible"""
        if not self.is_enabled:
            return False
        
        for client in self.clients.values():
            if client.is_connected and tool_name in client.available_tools:
                return True
        
        return False
    
    def get_tool_info(self, tool_name: str) -> Optional[MCPTool]:
        """Obtiene información de una herramienta específica"""
        if not self.is_enabled:
            return None
        
        for client in self.clients.values():
            if client.is_connected and tool_name in client.available_tools:
                return client.available_tools[tool_name]
        
        return None