from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class User(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    id: int
    name: Annotated[str, Field(min_length=1, max_length=80)]
    email: str | None = None

    @field_validator("email")
    @classmethod
    def lower(cls, v: str | None) -> str | None:
        return v.lower() if v else v
