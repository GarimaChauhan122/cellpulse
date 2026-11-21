# CellPulse – RAN KPI service with a production-style CI/CD pipeline

![CI/CD](https://github.com/GarimaChauhan122/cellpulse/actions/workflows/ci.yml/badge.svg)

A small FastAPI service that ingests radio-cell KPIs (PRB utilisation, throughput,
drop-call rate, latency) and raises alerts. The app is deliberately small and
telecom-flavoured; **the point of the repo is the delivery pipeline around it**.

## Pipeline (GitLab CI)
`verify → security → build → scan → deploy-staging → deploy-prod`

| Stage | What | Why |
|---|---|---|
| verify | ruff, pytest + coverage gate (85%), helm lint | fast feedback on every MR |
| security | Gitleaks, Bandit (SAST), pip-audit | shift-left security |
| build | Kaniko, multi-stage non-root image tagged with commit SHA | build once, immutable artifact |
| scan | Trivy (fails on HIGH/CRITICAL), Syft SBOM (CycloneDX) | supply-chain security |
| deploy-staging | Helm `--atomic` + smoke test verifying the deployed SHA | auto-rollback on failure |
| deploy-prod | manual gate, `resource_group` lock, 3 replicas | safe promotion |

Other features: pip caching, MR-only vs main-only jobs via `workflow:rules`,
interruptible jobs, JUnit + coverage reports in the MR UI, rolling update with
`maxUnavailable: 0`, probes, read-only root FS, Prometheus metrics, optional HPA.

## Pipeline (GitHub Actions) – `.github/workflows/ci.yml`
Same flow as the GitLab file, using GitHub-native pieces: matrix tests (py3.11/3.12), pip caching,
Docker layer cache, Trivy + SBOM, then a **throwaway kind cluster** per run where the exact built image is
deployed with Helm (`--atomic`) and smoke-tested. On `main`, publishing the image to GHCR waits for approval
via the `production` environment. Least-privilege `permissions`, concurrency cancel, Dependabot updates.

## Run locally
```
make dev && make test && make run     # API docs at :8080/docs
make kind                             # deploy to a local kind cluster via Helm
```

## Live dashboard (Prometheus + Grafana)
```
docker compose up --build      # or: make monitor
```
Grafana at http://localhost:3000 opens the *CellPulse - RAN KPI Overview* dashboard
(ingest rate, alerts by severity, PRB utilisation per cell, busiest cells). A simulator
container feeds the app with synthetic cell KPIs; Prometheus scrapes `/metrics/` every 5s.

## Ideas to extend (day 2+)
- Add Terraform for the cluster/namespace and run `plan` on MRs
- AI step: on job failure, send redacted log tail to an LLM and post a root-cause comment on the MR
- Pipeline analytics script (duration, failure rate, flaky tests) via the GitLab API
- Canary/blue-green deploy, DORA metrics dashboard
