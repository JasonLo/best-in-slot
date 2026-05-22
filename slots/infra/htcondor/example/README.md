# htcondor example

Two submit files:

- `train.sub` — single GPU job pulling a GHCR image.
- `array.sub` — 10-job array, one per shard.

```sh
# Validate syntax (needs CHTC access to actually submit):
condor_submit -dry-run /dev/stdout train.sub

# Submit (from a CHTC submit node):
mkdir -p logs
condor_submit train.sub
condor_q
condor_tail -f <job-id>
```

The Docker image referenced here should be built via [docker](../docker/) or [pixi](../pixi/) and pushed to GHCR via the [github-actions](../github-actions/) `publish-image.yml` workflow.
