from pydantic import BaseModel, Field, ConfigDict


class AiRequest(BaseModel):
    input_text: str
    context: dict = Field(default_factory=dict)


class AiResponse(BaseModel):
    model: str = "mock"
    confidence: float = 0.0
    result: dict = Field(default_factory=dict)


class AiHistoryItem(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: str
    execution_id: str
    insight_type: str
    model_name: str
    provider_name: str = "mock"
    prompt_version: str
    confidence: float
    input_json: dict = Field(default_factory=dict)
    output_json: dict = Field(default_factory=dict)
