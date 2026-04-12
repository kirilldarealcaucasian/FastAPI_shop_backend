# Docker Build and Run

Build all application images with Docker Buildx:

```bash
docker buildx bake -f docker-bake.hcl
```

Build and load images for local Docker engine:

```bash
docker buildx bake -f docker-bake.hcl --load
```

Run full stack:

```bash
docker compose up -d
```

Rebuild with Buildx and restart stack:

```bash
docker buildx bake -f docker-bake.hcl --load && docker compose up -d --force-recreate
```
