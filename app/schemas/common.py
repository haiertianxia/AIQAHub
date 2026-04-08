from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    success: bool = True
    data: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

