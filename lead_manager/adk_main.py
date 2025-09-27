import logging
import click
import common.config as config
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from .agent_executor import LeadManagerAgentExecutor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--host",
    default="localhost",
    help="Host to bind the server to.",
)
@click.option(
    "--port",
    default=config.DEFAULT_LEAD_MANAGER_PORT,
    help="Port to bind the server to.",
)
def main(host: str, port: int):
    """Runs the Lead Manager agent as an A2A server."""
    logger.info("Configuring Lead Manager A2A server...")

    # Define the Agent Card for Lead Manager
    try:
        agent_card = AgentCard(
            name="Lead Manager Agent",
            description="Simple Lead Manager Agent that processes search queries and sends WebSocket messages",
            url=f"http://{host}:{port}",
            version="1.0.0",
            capabilities=AgentCapabilities(
                streaming=False,
                pushNotifications=False,
            ),
            skills=[
                AgentSkill(
                    id="process_search",
                    name="Process Search Query",
                    description="Processes search queries and sends WebSocket messages to UI client",
                    examples=[
                        "Search for potential leads in the technology sector"
                    ],
                    tags=["search", "leads"],
                )
            ],
            defaultInputModes=["data"],
            defaultOutputModes=["data"],
        )
    except Exception as e:
        logger.exception("Error creating AgentCard")
        raise

    # Instantiate the Lead Manager AgentExecutor
    try:
        agent_executor = LeadManagerAgentExecutor()
    except Exception as e:
        logger.exception("Error initializing LeadManagerAgentExecutor")
        raise

    # Instantiate the A2AStarletteApplication
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=task_store
    )
    try:
        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )
    except Exception as e:
        logger.exception("Error initializing A2AStarletteApplication")
        raise

    # Start the Server
    import uvicorn

    logger.info(f"Starting Lead Manager A2A server on http://{host}:{port}/")
    uvicorn.run(app_builder.build(), host=host, port=port)

if __name__ == "__main__":
    main()