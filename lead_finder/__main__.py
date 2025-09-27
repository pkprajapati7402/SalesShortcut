import logging
import click
import common.config as defaults

# Attempt to import A2A/ADK dependencies
try:
    import uvicorn
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    from .lead_finder.agent import lead_finder_agent
    from .agent_executor import LeadFinderAgentExecutor
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host",
    default=defaults.DEFAULT_LEAD_FINDER_URL.split(":")[1].replace("//", ""),
    help="Host to bind the server to.",
)
@click.option(
    "--port",
    default=int(defaults.DEFAULT_LEAD_FINDER_URL.split(":")[2]),
    help="Port to bind the server to.",
)
def main(host: str, port: int):
    """Runs the LEAD FINDER ADK agent as an A2A server."""
    # Fallback to simple HTTP if ADK/A2A deps missing
    if not ADK_AVAILABLE:
        logger.warning(f"! ! ! LEAD FINDER ADK or A2A SDK dependencies not found ({missing_dep}), falling back to simple HTTP service.")
        return
    logger.info(f"Configuring LEAD FINDER A2A server...")
    
    try:
        agent_card = AgentCard(
            name=lead_finder_agent.name,
            description=lead_finder_agent.description,
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
            ),
            defaultInputModes=['text'],
            defaultOutputModes=['text'],
            skills=[
                AgentSkill(
                    id='process_search',
                    name='Search for Leads in a City',
                    description='Using Google Maps and Cluster search, find potential leads from the city\'s businesses which has no website presence.',
                    examples=[
                        "Search for potential leads in the technology sector in San Francisco",
                        "Find leads in San Francisco",
                    ],
                    tags=[],
                ),
                AgentSkill(
                    id='save_leads',
                    name='Save Leads to Database',
                    description='Saves the found leads to the database for further processing.',
                    examples=[
                        "Save leads found in San Francisco",
                        "Store leads in the database",
                        "Save leads for further processing",
                    ],
                    tags=[],
                )
            ],
        )
    except AttributeError as e:
        logger.error(
            f"Error accessing attributes from riskguard_adk_agent: {e}. Is riskguard/agent.py correct?"
        )
        raise

    try:
        agent_executor = LeadFinderAgentExecutor()
        
        task_store = InMemoryTaskStore()
        
        request_handler = DefaultRequestHandler(agent_executor, task_store)
        
        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler
        )
        
        logger.info(f"Starting LEAD FINDER A2A server on {host}:{port}")
        # Start the Server
        import uvicorn
    
        logger.info(f"Starting RiskGuard A2A server on http://{host}:{port}/")
        uvicorn.run(app_builder.build(), host=host, port=port)
            
    except Exception as e:
        logger.error(f"Failed to start LEAD FINDER A2A server: {e}")
        raise


if __name__ == '__main__':
    main()