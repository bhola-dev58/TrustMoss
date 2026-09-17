# TrustMoss — GitHub Secrets Setup for CI/CD

This document lists every GitHub repository secret required for CI/CD pipelines to function correctly.

---

## Required Secrets (GitHub Repository → Settings → Secrets and variables → Actions)

### Core CI (ci.yml) — No additional secrets needed
The core test pipeline uses **stub values** injected inline. No secrets to configure.

---

### Docker Registry Push (release.yml) — GHCR (Auto-configured)

| Secret | Value | Notes |
| :--- | :--- | :--- |
| `GITHUB_TOKEN` | Automatic | Provided by GitHub — do NOT create manually. Grants `packages: write` permission set in workflow `permissions:` block. |

> **Action required:** In your GitHub repo → Settings → Actions → General → Workflow permissions → set to **"Read and write permissions"**

---

### Docker Hub Push (release.yml) — Optional Secondary Registry

Only required if you want images pushed to Docker Hub in addition to GHCR.

| Secret Name | Where to Get It | Required? |
| :--- | :--- | :--- |
| `DOCKER_USERNAME` | Your Docker Hub username | Optional |
| `DOCKER_TOKEN` | Docker Hub → Account Settings → Security → New Access Token | Optional |

> If `DOCKER_USERNAME` is not set, the Docker Hub login step is automatically skipped.

---

## Creating a Versioned Release (Manual)

To trigger a **versioned release** (e.g. `v1.0.0`) with a proper GitHub Release and semver image tags:

```bash
# From the project root, on the main branch
git tag v1.0.0 -m "Release v1.0.0 — Production readiness: CI/CD, Secrets, Database"
git push origin v1.0.0
```

This triggers `release.yml` with `is_tagged_release=true`, which:
1. Pushes `ghcr.io/<owner>/trustmoss-*:v1.0.0` + `ghcr.io/<owner>/trustmoss-*:1.0` + `:1`
2. Creates a proper GitHub Release (not pre-release) with structured changelog

---

## GHCR Image Pull Commands (after first release)

```bash
# Pull all 6 images for production deployment
docker pull ghcr.io/<your-github-username>/trustmoss-gateway:latest
docker pull ghcr.io/<your-github-username>/trustmoss-guardrails:latest
docker pull ghcr.io/<your-github-username>/trustmoss-moss-service:latest
docker pull ghcr.io/<your-github-username>/trustmoss-evaluation:latest
docker pull ghcr.io/<your-github-username>/trustmoss-voice-agent:latest
docker pull ghcr.io/<your-github-username>/trustmoss-web:latest
```

> Replace `<your-github-username>` with your actual GitHub username (e.g. `bhola-dev58`).
