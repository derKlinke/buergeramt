from pydantic import BaseModel


class AgentResponse(BaseModel):
    response_text: str
