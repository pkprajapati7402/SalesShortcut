
from google.adk.agents.llm_agent import LlmAgent

from typing import Optional

from ..config import MODEL_THINK
from ..prompts import CONVERSATION_CLASSIFIER_PROMPT
from pydantic import BaseModel, Field

class ConversationClassificationResult(BaseModel):
    call_category: str = Field(description="The category of the call.")
    email: str = Field(description="The email address provided by the business owner or determined by the agent.")
    note: Optional[str] = Field(None, description="Any additional notes from the conversation.")

conversation_classifier_agent = LlmAgent(
    name="ConversationClassifierAgent",
    description="Agent that analyzes conversation results and classifies them into categories",
    model=MODEL_THINK,
    instruction=CONVERSATION_CLASSIFIER_PROMPT,
    output_schema=ConversationClassificationResult,
    output_key="call_category",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True
)
