# pixi cheatsheet

## Install pixi

```sh
curl -fsSL https://pixi.sh/install.sh | bash
```

## Commands

```sh
pixi init my-proj           # new project
pixi add pytorch cuda-cudnn # runtime dep
pixi add --pypi anthropic   # PyPI dep inside pixi env
pixi install                # materialise .pixi/envs/default
pixi run python -c "import torch"
pixi shell                  # activate (like conda activate)
pixi tree                   # dep graph
pixi update pytorch
```

## Minimal `pixi.toml`

```toml
[project]
name = "my-cuda-proj"
description = "GPU training on CHTC"
channels = ["pytorch", "nvidia", "conda-forge"]
platforms = ["linux-64"]
channel-priority = "strict"

[dependencies]
python = "3.12.*"
pytorch = { version = ">=2.5", channel = "pytorch" }
torchvision = { version = ">=0.20", channel = "pytorch" }
pytorch-cuda = { version = "12.4", channel = "pytorch" }
cuda-cudnn = "*"

[pypi-dependencies]
anthropic = ">=0.39"

[tasks]
train = "python -m my_proj.train"
nvidia-smi = "nvidia-smi"
```

## Docker (matches pixi-docker-chtc)

```dockerfile
FROM ghcr.io/prefix-dev/pixi:0.49.0-cuda12-bookworm

WORKDIR /app
COPY pixi.toml pixi.lock ./
RUN pixi install --frozen

COPY . .
ENV PATH="/app/.pixi/envs/default/bin:$PATH"
CMD ["pixi", "run", "train"]
```

## HTCondor submit (see htcondor slot)

```
universe                = docker
docker_image            = ghcr.io/jasonlo/my-cuda-proj:latest
request_gpus            = 1
queue 1
```
