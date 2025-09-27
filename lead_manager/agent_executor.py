import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part

from google.adk import Runner
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService, Session
from google.genai import types as genai_types

from .agent import root_agent as lead_manager_adk_agent

logger = logging.getLogger(__name__)


# Initialize logging to file
root_path = Path.cwd()
log_file = root_path / "lead_finder/lead_finder_agent.log"
def log_to_file(message: str):
    """Write log message to file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write('\n')
        f.write(f"[{timestamp}] {message}\n")
        f.write('\n')

# Clear previous logs and start fresh for this call
with open(log_file, 'w', encoding='utf-8') as f:
    f.write(f"=== LEAD FINDER AGENT's LOG - {datetime.now().isoformat()} ===\n\n")
    
class LeadManagerAgentExecutor(AgentExecutor):
    """Executes the Lead Manager ADK agent logic in response to A2A requests."""

    def __init__(self):
        self._adk_agent = lead_manager_adk_agent
        self._adk_runner = Runner(
            app_name="lead_manager_adk_runner",
            agent=self._adk_agent,
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
            artifact_service=InMemoryArtifactService(),
        )
        logger.info("LeadManagerAgentExecutor initialized with ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            task_updater.submit(message=context.message)

        task_updater.start_work(
            message=task_updater.new_agent_message(
                parts=[
                    Part(root=DataPart(data={"status": "Processing search query..."}))
                ]
            )
        )

        # Extract search query from context.message
        search_query: str | None = None
        ui_client_url = "http://localhost:8000"  # Default UI client URL

        if context.message and context.message.parts:
            for part_union in context.message.parts:
                part = part_union.root
                if isinstance(part, DataPart):
                    if "query" in part.data:
                        search_query = part.data["query"]
                    if "ui_client_url" in part.data:
                        ui_client_url = part.data["ui_client_url"]

        if search_query is None:
            logger.error(f"Task {context.task_id}: Missing search query in input")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[
                        Part(
                            root=DataPart(
                                data={"error": "Invalid input: Missing search query"}
                            )
                        )
                    ]
                )
            )
            return

        # Prepare input for ADK Agent
        agent_input_dict = {
            "query": search_query,
            "ui_client_url": ui_client_url
        }
        agent_input_json = json.dumps(agent_input_dict)
        adk_content = genai_types.Content(
            parts=[genai_types.Part(text=agent_input_json)]
        )

        # Ensure ADK Session Exists
        session_id_for_adk = context.context_id
        logger.info(f"Task {context.task_id}: Using ADK session_id: '{session_id_for_adk}'")

        session: Session | None = None
        if session_id_for_adk:
            try:
                session = await self._adk_runner.session_service.get_session(
                    app_name=self._adk_runner.app_name,
                    user_id="a2a_user",
                    session_id=session_id_for_adk,
                )
            except Exception as e:
                logger.exception(f"Task {context.task_id}: Exception during get_session: {e}")
                session = None

            if not session:
                logger.info(f"Task {context.task_id}: Creating new ADK session")
                try:
                    session = await self._adk_runner.session_service.create_session(
                        app_name=self._adk_runner.app_name,
                        user_id="a2a_user",
                        session_id=session_id_for_adk,
                        state={},
                    )
                    if session:
                        logger.info(f"Task {context.task_id}: Successfully created ADK session")
                except Exception as e:
                    logger.exception(f"Task {context.task_id}: Exception during create_session: {e}")
                    session = None

        if not session:
            error_message = f"Failed to establish ADK session for session_id '{session_id_for_adk}'"
            logger.error(f"Task {context.task_id}: {error_message}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[
                        Part(
                            root=DataPart(
                                data={"error": f"Internal error: {error_message}"}
                            )
                        )
                    ]
                )
            )
            return

        # Execute the ADK Agent
        try:
            logger.info(f"Task {context.task_id}: Calling ADK run_async")
            final_result = {"status": "completed", "query": search_query}
            
            async for event in self._adk_runner.run_async(
                user_id="a2a_user",
                session_id=session_id_for_adk,
                new_message=adk_content,
            ):
                log_entry = f" ** - - - - - ** \n [Event] Author: {event.author}, \n Type: {type(event).__name__}, \n Final: {event.is_final_response()}, \n Content: {event.content}"
                log_to_file(log_entry)
                
                if event.is_final_response():
                    if event.content and event.content.parts:
                        text_part = next(
                            (
                                p
                                for p in event.content.parts
                                if hasattr(p, "text") and p.text
                            ),
                            None,
                        )
                        if text_part:
                            final_result["message"] = text_part.text

            task_updater.add_artifact(
                parts=[Part(root=DataPart(data=final_result))],
                name="search_result",
            )
            task_updater.complete()

        except Exception as e:
            logger.exception(f"Task {context.task_id}: Error running Lead Manager ADK agent: {e}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": f"ADK Agent error: {e}"}))]
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        logger.warning(f"Cancellation not implemented for Lead Manager task: {context.task_id}")
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        task_updater.failed(
            message=task_updater.new_agent_message(
                parts=[Part(root=DataPart(data={"error": "Task cancelled"}))]
            )
        )