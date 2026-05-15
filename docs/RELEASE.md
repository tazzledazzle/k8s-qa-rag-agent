# Release: images, CI, and production tags

This document satisfies **REL-01**: how container images are built in CI, how **base** vs **prod** Kustomize references them, and how operators should pin **immutable** tags or digests before production.

## CI build matrix

The GitHub Actions workflow **[`.github/workflows/ci.yml`](../.github/workflows/ci.yml)** defines a **`build`** job that **`needs: [test, git-watcher, otel-config]`** and runs on **push** and **pull_request** to **`main`** and **`develop`**. It builds **four** service images (tags use **`${{ github.sha }}`** in CI):

| Service | Dockerfile | CI image name (example) | Local build (from repo root) |
|---------|------------|-------------------------|------------------------------|
| Indexer | `services/indexer/Dockerfile` | `indexer:<sha>` | `docker build -f services/indexer/Dockerfile -t indexer:local .` |
| Retriever | `services/retriever/Dockerfile` | `retriever:<sha>` | `docker build -f services/retriever/Dockerfile -t retriever:local .` |
| QA agent | `services/qa_agent/Dockerfile` | `qa-agent:<sha>` | `docker build -f services/qa_agent/Dockerfile -t qa-agent:local .` |
| Git watcher | `services/git-watcher/Dockerfile` | `git-watcher:<sha>` | `docker build -f services/git-watcher/Dockerfile -t git-watcher:local .` |

**Also validated in CI:** **`otel-config`** job runs **`scripts/validate-otel-config.sh`** (OpenTelemetry Collector config). Python **`test`** job runs **flake8**, **black**, **mypy**, **pytest**.

## Base vs production images

- **`k8s/base/kustomization.yaml`** uses the **`images:`** transformer with **`newTag: latest`** for the four app images — convenient for **local / portfolio** builds where you load images into kind/minikube manually.
- **`k8s/overlays/prod/kustomization.yaml`** overrides those tags with **non-`latest`** values (portfolio default **`0.1.0`** as a **placeholder**). **Replace** `newTag` (or `newName` with full registry path) with your **registry + digest or release tag** before relying on prod.

## Qdrant

- **Base** uses **`qdrant/qdrant:latest`** for developer velocity.
- **Prod** overlay pins **`qdrant/qdrant:v1.16.2`** (verify upgrades against [Qdrant releases](https://github.com/qdrant/qdrant/releases) before bumping).

## Setting images for a prod deploy

The **`images:`** entries in **`k8s/overlays/prod/kustomization.yaml`** use Kustomize **`name`** keys that match the image references in Deployments / StatefulSet (`qa-agent`, `retriever`, `indexer`, `git-watcher`, **`qdrant/qdrant`**).

From repo root, after editing tags or registry:

```bash
cd k8s/overlays/prod
kubectl kustomize . > /tmp/prod-rendered.yaml
# Inspect image: lines, then apply with your normal GitOps / kubectl flow.
```

**Examples** (run from `k8s/overlays/prod`; adjust registry host):

```bash
kustomize edit set image qa-agent=myregistry.example/qa-agent:v2026.05.15
kustomize edit set image retriever=myregistry.example/retriever:v2026.05.15
kustomize edit set image indexer=myregistry.example/indexer:v2026.05.15
kustomize edit set image git-watcher=myregistry.example/git-watcher:v2026.05.15
kustomize edit set image qdrant/qdrant=qdrant/qdrant:v1.16.2
```

CI builds tag **`${{ github.sha }}`** — many teams **retag** or **mirror** that digest into a production registry and set **`newName`/`newTag`** (or use Flux/ImageUpdateAutomation) so clusters never pull anonymous **`latest`**.

## External CD (optional)

If **Flux**, **Argo CD Image Updater**, or another controller owns image versions, keep **`k8s/overlays/prod/kustomization.yaml`** as a **baseline** and document that **live** pins live in the CD layer — but the verifier must still find an **explicit** prod policy in git or linked runbooks.
