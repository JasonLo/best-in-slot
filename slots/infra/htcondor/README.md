# htcondor

**Slot**: Batch / GPU job scheduler for UW CHTC. Matches `pixi-docker-chtc` and `chtc_condor`.

## Why htcondor

CHTC (Center for High-Throughput Computing) runs on HTCondor; if you're submitting to CHTC GPU pools, this is the interface. Submit description files (`.sub`) are declarative — same shape whether the job is one node or a 1000-job array.

## Conventions

- One `submit.sub` per job kind (`train.sub`, `eval.sub`).
- Always set `universe = docker` and point `docker_image` at a GHCR image — never rely on cluster-local conda.
- Build the image with [pixi](../pixi/) when CUDA is involved; with [docker](../docker/) uv base image otherwise.
- Request what you need (`request_gpus`, `request_cpus`, `request_memory`, `request_disk`) — no defaults.
- Log paths use `$(Cluster)` and `$(Process)` so array jobs don't collide.
- `queue N` for arrays; pair with `args = --shard $(Process)` style.

## Alternatives considered

- **slurm** — different cluster ecosystem; not what UW CHTC uses.
- **k8s Job** — own infra cost; only worth it when you also have a service mesh.
- **Local docker / single machine** — for sub-GPU-day work, skip the cluster.

## Gotchas

- `transfer_input_files` lists are explicit — Condor doesn't auto-grab your working dir.
- Large datasets via [Pelican](https://pelicanplatform.org) (CHTC default), not via `transfer_input_files`.
- BadgerCompute job submissions wrap Condor — see `UW-Madison-DSI/badgercompute-binder-example`.
- Stdout / stderr go to files named in the `output =` and `error =` directives, not to your terminal.
