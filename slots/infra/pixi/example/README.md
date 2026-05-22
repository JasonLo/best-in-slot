# pixi example

Minimal CPU-only pixi project. For GPU workloads swap `numpy` for `pytorch` + `pytorch-cuda` and use the CUDA base image (see Dockerfile comment).

```sh
pixi install
pixi run hello
# → numpy 2.x.y

# build container:
docker build -t pixi-example .
docker run --rm pixi-example
```

Submit to CHTC: see [htcondor](../htcondor/) for the `.sub` file shape.
