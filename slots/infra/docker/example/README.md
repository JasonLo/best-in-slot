# docker example

Tiny FastAPI service shipped via the canonical uv-based Dockerfile.

```sh
uv lock                       # generate uv.lock if missing
docker build -t docker-example .
docker run --rm -p 8000:8000 docker-example
# then:
curl http://localhost:8000/healthz
```
