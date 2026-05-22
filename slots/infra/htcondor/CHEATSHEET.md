# htcondor cheatsheet

## Submit a docker-based GPU job

```
# train.sub
universe                = docker
docker_image            = ghcr.io/jasonlo/my-cuda-proj:latest

executable              = /bin/bash
arguments               = -lc "pixi run train --epochs 10"

output                  = logs/train.$(Cluster).$(Process).out
error                   = logs/train.$(Cluster).$(Process).err
log                     = logs/train.$(Cluster).log

request_gpus            = 1
request_cpus            = 4
request_memory          = 16 GB
request_disk            = 20 GB

requirements            = (HAS_CHTC_GROUP =?= True)
+WantGPULab             = true

queue 1
```

## Submit, watch, kill

```sh
condor_submit train.sub
condor_q                            # your jobs
condor_q --better-analyze <id>      # why is this not running?
condor_tail -f <id>                 # live stdout
condor_rm <id>                      # kill
```

## Array job (10 shards)

```
arguments               = --shard $(Process)
queue 10
```

## Pelican input

```
# Inside the container, the data is at pelican://...
# Tell Condor to NOT transfer it via condor file transfer.
should_transfer_files   = NO
```

…then in your training code:

```python
import pelicanfs
fs = pelicanfs.PelicanFileSystem()
with fs.open("pelican://uwdf-director.chtc.wisc.edu/wisc.edu/dsi/...") as f:
    ...
```

## Local dry-run validate

```sh
condor_submit -dry-run /dev/stdout train.sub
```
