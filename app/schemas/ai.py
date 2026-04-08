from pydantic import BaseModel, Field


class AiRequest(BaseModel):
    input_text: str
    context: dict = Field(default_factory=dict)


class AiResponse(BaseModel):
    model: str = "mock"
    confidence: float = 0.0
    result: dict = Field(default_factory=dict)

