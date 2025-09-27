# Lead Manager A2A Agent
# Optional imports - only load if dependencies are available
try:
    from . import agent, agent_executor
except ImportError:
    # ADK dependencies not available, use simple version
    pass