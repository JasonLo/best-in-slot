# For real CUDA workloads, swap base to:
#   FROM ghcr.io/prefix-dev/pixi:0.49.0-cuda12-bookworm
# This example uses the CPU image so it builds anywhere.
FROM ghcr.io/prefix-dev/pixi:0.49.0-bookworm

WORKDIR /app
COPY pixi.toml pixi.lock* ./
RUN pixi install --frozen || pixi install   # accept first-run without lock

COPY . .
ENV PATH="/app/.pixi/envs/default/bin:$PATH"
CMD ["pixi", "run", "hello"]
