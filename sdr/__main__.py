#!/usr/bin/env python3
"""SDR Agent Service"""
import logging
import click
import os
import common.config as defaults

# Attempt to import A2A/ADK dependencies
try:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    from starlette.requests import Request
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill
    from .sdr.agent import root_agent
    from .agent_executor import SDRAgentExecutor
    # Imports for endpoint logic
    from .sdr.callbacks import send_sdr_update_to_ui
    from .sdr.sub_agents.outreach_email_agent.sub_agents.website_creator.tools.human_creation_tool import send_ui_notification, submit_human_response

    ADK_AVAILABLE = True
except ImportError as e:
    from starlette.applications import Starlette # Dummy for error case
    ADK_AVAILABLE = False
    missing_dep = e

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==============================================================================
# --- Create the `app` object in the global scope for Uvicorn ---
# ==============================================================================

try:
    if not ADK_AVAILABLE:
        raise ImportError(f"A2A/ADK dependency missing: {missing_dep}")

    SDR_PUBLIC_URL = os.environ.get("SDR_SERVICE_URL", "http://localhost:8084")

    logger.info(f"Configuring SDR Agent with public URL: {SDR_PUBLIC_URL}")

    agent_card = AgentCard(
        name=root_agent.name,
        description=root_agent.description,
        url=SDR_PUBLIC_URL,
        version="1.0.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        defaultInputModes=['text', 'json', 'data'],
        defaultOutputModes=['text'],
        skills=[
            AgentSkill(
                id='research_leads', name='Search the internet for Leads',
                description='Using Google Search, gather information about potential lead from the internet.',
                examples=["Find information about business named 'Acme Corp' in San Francisco"], tags=['research', 'business'],
            ),
            AgentSkill(
                id='proposal_generation', name='Generate Proposal for Lead',
                description='Generate a proposal for the lead based on the gathered information.',
                examples=["Generate a proposal for 'Acme Corp' based on the gathered information"], tags=['proposal', 'business'],
            ),
            AgentSkill(
                id='outreach_phone_caller', name='Outreach Phone Caller',
                description='Make a phone call to the lead to discuss the proposal.',
                examples=["Call 'Acme Corp' to discuss the proposal"], tags=['outreach', 'phone'],
            ),
            AgentSkill(
                id='lead_engagement_saver', name='Lead Engagement Saver',
                description='Save the lead engagement information for future reference.',
                examples=["Save the engagement information for 'Acme Corp'"], tags=['engagement', 'lead'],
            ),
            AgentSkill(
                id='conversation_classifier', name='Conversation Classifier',
                description='Classify the conversation to determine the next steps.',
                examples=["Classify the conversation with 'Acme Corp' to determine if they are interested"], tags=['classification', 'conversation'],
            ),
            AgentSkill(
                id='sdr_router', name='SDR Router',
                description='Route the lead to the appropriate agent based on the conversation classification.',
                examples=["Route the lead from 'Acme Corp' to the appropriate agent"], tags=['routing', 'lead'],
            ),
            AgentSkill(
                id='check_availability', name='Check Calendar Availability',
                description="Checks a user's availability for a time using their Google Calendar",
                tags=['calendar'], examples=['Am I free from 10am to 11am tomorrow?'],
            ),
        ]
    )

    agent_executor = SDRAgentExecutor()
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(agent_executor, task_store)
    a2a_app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    app = a2a_app_builder.build()

    # --- Define and append all routes to the global `app` object ---

    # --- FIX: Define and INSERT the health check FIRST to ensure it is not overridden ---
    async def health_check(request: Request):
        """Simple health check endpoint"""
        return JSONResponse({
            'status': 'healthy',
            'message': 'SDR service is running',
            'endpoints': [
                '/test/ui-callback',
                '/test/human-creation',
                '/api/human-input/{request_id}',
                '/authenticate'
            ]
        })
    app.routes.insert(0, Route(path='/health', methods=['GET'], endpoint=health_check))


    # --- Now add all OTHER routes as before ---
    app.routes.append(
        Route(
            path='/authenticate',
            methods=['GET'],
            endpoint=lambda request: agent_executor.on_auth_callback(
                str(request.query_params.get('state')),
                str(request.url)
            ),
        )
    )

    async def human_input_callback(request: Request):
        request_id = request.path_params.get('request_id')
        try:
            data = await request.json()
        except Exception:
            return JSONResponse({'status': 'failed', 'message': 'Invalid JSON'}, status_code=400)
        url = data.get('url') or data.get('response')
        if not request_id or not url:
            return JSONResponse({'status': 'failed', 'message': 'Missing request_id or url'}, status_code=400)
        success = submit_human_response(request_id, url)
        if success:
            return JSONResponse({'status': 'success', 'request_id': request_id})
        return JSONResponse({'status': 'failed', 'message': 'Invalid request ID or request not pending'}, status_code=404)

    app.routes.append(
        Route(path='/api/human-input/{request_id}', methods=['POST'], endpoint=human_input_callback)
    )

    async def test_ui_callback(request: Request):
        """Test endpoint to trigger send_sdr_update_to_ui functionality"""
        try:
            test_business_data = {"id": "test-123", "name": "Test Business Corp", "address": "123 Main St, San Francisco, CA, 94105", "phone": "+1234567890", "email": "test@testbusiness.com"}
            test_email_result = {"status": "success", "message": "Test email sent", "crafted_email": {"to": "test@testbusiness.com", "subject": "Test Subject - SDR Communication Test", "body": "This is a test email body."}}
            success = send_sdr_update_to_ui(test_business_data, test_email_result)
            return JSONResponse({'status': 'success' if success else 'failed', 'message': 'UI callback test completed', 'ui_callback_success': success})
        except Exception as e:
            logger.error(f"Test UI callback error: {e}")
            return JSONResponse({'status': 'error', 'message': f'Test failed: {str(e)}'}, status_code=500)

    app.routes.append(
        Route(path='/test/ui-callback', methods=['GET'], endpoint=test_ui_callback)
    )

    async def test_human_creation(request: Request):
        """Test endpoint to trigger human_creation functionality"""
        try:
            prompt = request.query_params.get('prompt', 'Create a test website for communication testing')
            test_request_id = f"test-{hash(prompt) % 100000}"
            success = await send_ui_notification(test_request_id, prompt)
            return JSONResponse({'status': 'success' if success else 'failed', 'message': 'Human creation test completed', 'test_data': {'request_id': test_request_id, 'prompt': prompt}, 'ui_notification_success': success})
        except Exception as e:
            logger.error(f"Test human creation error: {e}")
            return JSONResponse({'status': 'error', 'message': f'Test failed: {str(e)}'}, status_code=500)

    app.routes.append(
        Route(path='/test/human-creation', methods=['GET'], endpoint=test_human_creation)
    )


except Exception as e:
    logger.error(f"FATAL: Failed to build the SDR application object. {e}", exc_info=True)
    # Create a dummy app that reports the error so the container doesn't crash silently
    app = Starlette(debug=True)
    @app.route("/health")
    async def error_app(request: Request):
        return JSONResponse({"status": "error", "message": "Application failed to initialize", "error": str(e)}, status_code=500)


# ==============================================================================
# --- The `main` function is now only a local development runner ---
# ==============================================================================

@click.command()
@click.option("--host", default="127.0.0.1", help="Host to bind the server to for local development.")
@click.option("--port", default=8084, type=int, help="Port to bind the server to for local development.")
def main(host: str, port: int):
    """
    Runs the SDR ADK agent LOCALLY for development.
    In production (Docker/Cloud Run), Uvicorn is called directly.
    """
    logger.info(f"Starting development server on http://{host}:{port}/")
    uvicorn.run("sdr.__main__:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    main()