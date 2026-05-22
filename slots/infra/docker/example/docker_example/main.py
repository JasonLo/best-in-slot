from fastapi import FastAPI

app = FastAPI(title="docker-example")


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"msg": "hello from docker"}
