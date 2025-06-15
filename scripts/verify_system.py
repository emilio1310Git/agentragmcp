"""Verificación completa del sistema dinámico"""

import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def main():
    print("🔍 VERIFICACIÓN COMPLETA DEL SISTEMA")
    print("="*50)
    
    try:
        from agentragmcp.core.dynamic_config import config_manager
        
        # 1. Verificar archivos de configuración
        print("\n📁 Verificando archivos...")
        config_path = Path("data/configs")
        rags_path = config_path / "rags"
        agents_file = config_path / "agents.yaml"
        
        print(f"   Config dir: {'✅' if config_path.exists() else '❌'} {config_path}")
        print(f"   RAGs dir: {'✅' if rags_path.exists() else '❌'} {rags_path}")
        print(f"   Agents file: {'✅' if agents_file.exists() else '❌'} {agents_file}")
        
        # 2. Descubrir configuraciones
        print("\n🔍 Descubriendo configuraciones...")
        discovered = config_manager.discover_rag_configs()
        print(f"   RAGs descubiertos: {len(discovered)} → {discovered}")
        
        # 3. Crear ejemplos si no existen
        if not discovered:
            print("\n📋 Creando configuraciones de ejemplo...")
            config_manager.create_sample_configs()
            discovered = config_manager.discover_rag_configs()
            print(f"   RAGs creados: {len(discovered)} → {discovered}")
        
        # 4. Cargar configuraciones
        print("\n🔧 Cargando configuraciones...")
        all_configs = config_manager.get_all_rag_configs()
        enabled = config_manager.get_enabled_topics()
        
        print(f"   RAGs cargados: {len(all_configs)}")
        print(f"   RAGs habilitados: {len(enabled)} → {enabled}")
        
        # 5. Verificar agentes
        print("\n🤖 Verificando agentes...")
        test_agents = ['plants', 'pathology', 'general']
        loaded_agents = []
        
        for agent_name in test_agents:
            config = config_manager.load_agent_config(agent_name)
            if config:
                print(f"   ✅ {agent_name}: {config.description[:50]}...")
                loaded_agents.append(agent_name)
            else:
                print(f"   ❌ {agent_name}: No configurado")
        
        # 6. Verificar sistema dinámico
        print("\n⚙️  Verificando DynamicAgentSystem...")
        try:
            from agentragmcp.api.app.services.dynamic_agent_system import DynamicAgentSystem
            system = DynamicAgentSystem()
            health = system.health_check()
            
            print(f"   Estado: {health['status']}")
            print(f"   Agentes activos: {health.get('enabled_agents', 'N/A')}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 7. Resumen
        print(f"\n📊 RESUMEN:")
        print(f"   ✅ Configuraciones descubiertas: {len(discovered)}")
        print(f"   ✅ RAGs cargados: {len(all_configs)}")
        print(f"   ✅ RAGs habilitados: {len(enabled)}")
        print(f"   ✅ Agentes configurados: {len(loaded_agents)}")
        
        if len(discovered) > 0 and len(enabled) > 0 and len(loaded_agents) > 0:
            print(f"\n🎉 ¡Sistema dinámico funcionando correctamente!")
            return True
        else:
            print(f"\n⚠️  Sistema parcialmente configurado")
            return False
            
    except Exception as e:
        print(f"\n❌ Error durante verificación: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)