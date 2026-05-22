from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="fastapi-example")


class Hello(BaseModel):
    name: str


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/hello")
def hello(body: Hello) -> dict[str, str]:
    return {"msg": f"hello, {body.name}"}
