import json
import logging
from typing import Any
from datetime import datetime
from pathlib import Path

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import DataPart, Part, TaskState

# Make sure you have a shared config for the artifact name
from common.config import DEFAULT_LEAD_FINDER_ARTIFACT_NAME, DEFAULT_UI_CLIENT_URL
from google.adk import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.adk.artifacts import InMemoryArtifactService
from google.genai import types as genai_types

from .lead_finder.agent import lead_finder_agent

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

class LeadFinderAgentExecutor(AgentExecutor):
    """Executes the Lead Finder ADK agent logic in response to A2A requests."""

    def __init__(self):
        self._adk_agent = lead_finder_agent
        self._adk_runner = Runner(
            app_name="lead_finder_adk_runner",
            agent=self._adk_agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
        )
        logger.info("LeadFinderAgentExecutor initialized with ADK Runner.")

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        
        logger.info(f"DEBUG: Context message parts: {[str(part) for part in context.message.parts]}")

        if not context.current_task:
            task_updater.submit(message=context.message)

        task_updater.start_work(
            message=task_updater.new_agent_message(
                parts=[
                    Part(root=DataPart(data={"status": "Processing city search request..."}))
                ]
            )
        )

        # Extract city from context.message - IMPROVED EXTRACTION
        city_name: str | None = None
        ui_client_url = DEFAULT_UI_CLIENT_URL

        if context.message and context.message.parts:
            for part_union in context.message.parts:
                part = part_union.root
                if isinstance(part, DataPart):
                    # Try multiple keys for city
                    if "city" in part.data:
                        city_name = part.data["city"]
                    elif "query" in part.data:
                        city_name = part.data["query"]  # Assuming query contains city
                    elif "search_query" in part.data:
                        city_name = part.data["search_query"]
                    
                    if "ui_client_url" in part.data:
                        ui_client_url = part.data["ui_client_url"]

        if city_name is None:
            logger.error(f"Task {context.task_id}: Missing city name in input")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[
                        Part(
                            root=DataPart(
                                data={"error": "Invalid input: Missing city name"}
                            )
                        )
                    ]
                )
            )
            return

        # Prepare input for ADK Agent with clear structure
        agent_input_dict = {
            "city": city_name,
            "ui_client_url": ui_client_url,
            "operation": "find_leads"
        }
        
        # Create a clear user message for the agent
        user_message = f"Find potential business leads in {city_name}"
        
        # Create both text and structured data
        adk_content = genai_types.Content(
            parts=[
                genai_types.Part(text=user_message),
                genai_types.Part(text=json.dumps(agent_input_dict))
            ]
        )

        # [Rest of the session handling code remains the same...]
        session_id_for_adk = context.context_id
        logger.info(f"Task {context.task_id}: Using ADK session_id: '{session_id_for_adk}' for city: '{city_name}'")

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
                logger.info(f"Task {context.task_id}: Creating new ADK session for city: {city_name}")
                try:
                    session = await self._adk_runner.session_service.create_session(
                        app_name=self._adk_runner.app_name,
                        user_id="a2a_user",
                        session_id=session_id_for_adk,
                        state={"city": city_name},  # Store city in session state
                    )
                    if session:
                        logger.info(f"Task {context.task_id}: Successfully created ADK session with city: {city_name}")
                except Exception as e:
                    logger.exception(f"Task {context.task_id}: Exception during create_session: {e}")
                    session = None

        if not session:
            error_message = f"Failed to establish ADK session for city '{city_name}'"
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
            logger.info(f"Task {context.task_id}: Calling ADK run_async for city: {city_name}")
            final_result = {"status": "completed", "city": city_name, "businesses": []}
            
            async for event in self._adk_runner.run_async(
                user_id="a2a_user",
                session_id=session_id_for_adk,
                new_message=adk_content,
            ):
                log_entry = f" ** - - - - - ** \n [Event] Author: {event.author}, \n Type: {type(event).__name__}, \n Final: {event.is_final_response()}, \n Content: {event.content}"
                log_to_file(log_entry)
                
                if event.is_final_response():
                    if event.content and event.content.parts:
                        # Look for function calls with business data
                        for part in event.content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                if part.function_call.name == "final_lead_results":
                                    businesses = part.function_call.args.get("businesses", [])
                                    final_result["businesses"] = businesses
                                    final_result["count"] = len(businesses)
                                    logger.info(f"Task {context.task_id}: Found {len(businesses)} businesses for {city_name}")
                            elif hasattr(part, "text") and part.text:
                                final_result["message"] = part.text

            task_updater.add_artifact(
                parts=[Part(root=DataPart(data=final_result))],
                name="lead_search_results",
            )
            task_updater.complete()

        except Exception as e:
            logger.exception(f"Task {context.task_id}: Error running Lead Finder ADK agent for city {city_name}: {e}")
            task_updater.failed(
                message=task_updater.new_agent_message(
                    parts=[Part(root=DataPart(data={"error": f"ADK Agent error: {e}"}))]
                )
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        logger.warning(f"Cancellation not implemented for Lead Finder task: {context.task_id}")
        task_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        task_updater.failed(
            message=task_updater.new_agent_message(
                parts=[Part(root=DataPart(data={"error": "Task cancelled"}))]
            )
        )