# pydantic cheatsheet

## Basic model

```python
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


u = User.model_validate({"id": 1, "name": "Jason", "email": "J@WISC.EDU"})
print(u.model_dump())            # {'id': 1, 'name': 'Jason', 'email': 'j@wisc.edu'}
print(u.model_dump_json())
```

## Discriminated unions (tagged variants)

```python
from typing import Annotated, Literal, Union
from pydantic import BaseModel, Field, Tag

class Cat(BaseModel):
    kind: Literal["cat"]
    purr: bool

class Dog(BaseModel):
    kind: Literal["dog"]
    bark: bool

Pet = Annotated[Union[Cat, Dog], Field(discriminator="kind")]
```

## JSON schema

```python
print(User.model_json_schema())
```

## From / to dict

```python
data = u.model_dump()              # dict
js = u.model_dump_json(indent=2)   # str
parsed = User.model_validate_json(js)
```
