from agentragmcp.api.app.services.dynamic_agent_system import ConfigurableAgent

class MiAgentePersonalizado(ConfigurableAgent):
    def can_handle(self, question: str, context=None) -> float:
        # Tu lógica personalizada
        base_confidence = super().can_handle(question, context)
        # Añadir lógica específica...
        return base_confidence
    
    def process(self, question: str, session_id: str, **kwargs):
        # Tu procesamiento personalizado
        return self.rag_service.query(...)