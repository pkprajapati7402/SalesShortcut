"""
Specification Status Checker Agent - Custom agent that implements iterative refinement logic.
"""

import logging
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.base_agent import BaseAgent
from typing import AsyncGenerator


logger = logging.getLogger(__name__)


class SpecStatusCheckerAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("quality_status", "fail")
        if not status:
            logger.warning("Quality status not found in session state, defaulting to 'fail'")
            status = "fail"
        should_stop = (status == "pass")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))
