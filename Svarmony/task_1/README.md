# Task 1

Instruction for this task can be found in the markdown file below.
- [Instruction](instruction.md)

In the file below are my general notes on the assignment.
- [Notes](notes.md)


# Build
> How to build

Podman

```
podman-compose up -d
```

Docker

```
docker compose up -d
```

All logs will be in:
```
docker-data/tester.log
```

You can live watch this log with linux command:
```sh
tail -f docker-data/tester.log
```

# Software versions

- Go v1.19
- Docker engine v23.0
- Docker compose plugin v2.16
- Podman engine v4.3
- Podman compose v1.0