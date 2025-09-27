
from google.adk.auth import AuthConfig
import asyncio
from google.adk.events import Event


# --- Helper Functions ---
async def get_user_input(prompt: str) -> str:
    """
    Asynchronously prompts the user for input in the console.

    Uses asyncio's event loop and run_in_executor to avoid blocking the main
    asynchronous execution thread while waiting for synchronous `input()`.

    Args:
        prompt: The message to display to the user.

    Returns:
        The string entered by the user.
    """
    loop = asyncio.get_event_loop()
    # Run the blocking `input()` function in a separate thread managed by the executor.
    return await loop.run_in_executor(None, input, prompt)


def is_pending_auth_event(event: Event) -> bool:
    """
    Checks if an ADK Event represents a request for user authentication credentials.

    The ADK framework emits a specific function call ('adk_request_credential')
    when a tool requires authentication that hasn't been previously satisfied.

    Args:
        event: The ADK Event object to inspect.

    Returns:
        True if the event is an 'adk_request_credential' function call, False otherwise.
    """
    # Safely checks nested attributes to avoid errors if event structure is incomplete.
    return (
        event.content
        and event.content.parts
        and any(
            part.function_call
            and part.function_call.name == 'adk_request_credential'
            for part in event.content.parts
        )
    )


def get_function_call_id(event: Event) -> str:
    """
    Extracts the unique ID of the function call from an ADK Event.

    This ID is crucial for correlating a function *response* back to the specific
    function *call* that the agent initiated to request for auth credentials.

    Args:
        event: The ADK Event object containing the function call.

    Returns:
        The unique identifier string of the function call.

    Raises:
        ValueError: If the function call ID cannot be found in the event structure.
    """
    if (
        event
        and event.content
        and event.content.parts
    ):
        for part in event.content.parts:
            if part.function_call and part.function_call.id:
                return part.function_call.id
    # If the ID is missing, raise an error indicating an unexpected event format.
    raise ValueError(f'Cannot get function call id from event {event}')


def get_function_call_auth_config(event: Event) -> AuthConfig:
    """
    Extracts the authentication configuration details from an 'adk_request_credential' event.

    Client should use this AuthConfig to necessary authentication details (like OAuth codes and state)
    and sent it back to the ADK to continue OAuth token exchanging.

    Args:
        event: The ADK Event object containing the 'adk_request_credential' call.

    Returns:
        An AuthConfig object populated with details from the function call arguments.

    Raises:
        ValueError: If the 'auth_config' argument cannot be found in the event.
    """
    if (
        event
        and event.content
        and event.content.parts
    ):
        for part in event.content.parts:
            if (
                part.function_call
                and part.function_call.name == 'adk_request_credential'
                and part.function_call.args
                and part.function_call.args.get('authConfig')
            ):
                return AuthConfig(
                    **part.function_call.args.get('authConfig')
                )
                
    raise ValueError(f'Cannot get auth config from event {event}')