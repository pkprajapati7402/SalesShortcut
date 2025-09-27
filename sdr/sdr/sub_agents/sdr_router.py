"""
SDR Router Agent for routing leads based on conversation classification results.
"""

import logging
from typing import AsyncGenerator
from typing_extensions import override

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)


class SDRRouter(BaseAgent):
    """
    A custom agent that triggers either an Email Agent or a SaveToDatabase Agent
    based on a boolean flag in the session state ('call_category').
    """

    email_agent: BaseAgent
    save_to_database_agent: BaseAgent

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self, name: str, email_agent: BaseAgent, save_to_database_agent: BaseAgent
    ):
        """
        Initializes the SDRRouter.
        Args:
            name: The name of the agent.
            email_agent: The agent responsible for sending emails.
            save_to_database_agent: The agent responsible for saving to the database.
        """
        # Define the sub_agents list for the framework
        sub_agents_list = [email_agent, save_to_database_agent]

        super().__init__(
            name=name,
            email_agent=email_agent,
            save_to_database_agent=save_to_database_agent,
            sub_agents=sub_agents_list,  # Pass the sub_agents list directly
        )

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        """
        Implements the conditional outreach logic.
        Checks 'call_category' in session state and triggers the appropriate sub-agent.
        """
        logger.info(f"[{self.name}] Starting outreach workflow.")

        call_category = ctx.session.state.get("call_category")

        if call_category is None:
            logger.error(
                f"[{self.name}] 'call_category' not found in session state. Aborting outreach."
            )
            # Corrected: Use the Event constructor directly
            yield Event(
                content=types.Content(
                    parts=[
                        types.Part(
                            text="Outreach failed: Classifier result missing in session state."
                        )
                    ]
                ),
                author=self.name,
            )
            return

        logger.info(
            f"[{self.name}] Retrieved call_category: {call_category}"
        )

        if call_category:  # If True, trigger EmailAgent
            logger.info(f"[{self.name}] Classifier result is True. Triggering EmailAgent...")
            async for event in self.email_agent.run_async(ctx):
                logger.info(f"[{self.name}] Event from EmailAgent: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event
        else:  # If False, trigger SaveToDatabaseAgent
            logger.info(f"[{self.name}] Classifier result is False. Triggering SaveToDatabaseAgent...")
            async for event in self.save_to_database_agent.run_async(ctx):
                logger.info(f"[{self.name}] Event from SaveToDatabaseAgent: {event.model_dump_json(indent=2, exclude_none=True)}")
                yield event

        logger.info(f"[{self.name}] Outreach workflow finished.")