# Architecture

This lab is built around one small service and the operational systems needed to observe it.

## Runtime Flow

```text
Client / load simulator
   |
   | HTTP requests
   v
Kubernetes Service: sre-app
   |
   v
Deployment: sre-app
   |-- init-check container
   |-- sre-app container (FastAPI)
   |-- log-tail sidecar
   |
   | /healthz, /readyz, /metrics
   v
Prometheus scrape endpoint
```

The app runs in the `sre-demo` namespace with two replicas. Kubernetes uses `/healthz` for liveness and `/readyz` for readiness, while Prometheus scrapes `/metrics`.

## Observability Flow

```text
FastAPI app
   |
   | prometheus-fastapi-instrumentator
   v
/metrics endpoint
   |
   | ServiceMonitor selects Service label app=sre-app
   v
Prometheus
   |
   | evaluates PrometheusRule
   v
Alerts
   |
   v
Grafana dashboard
```

The dashboard focuses on RED signals and saturation:

- Request rate
- 5xx error rate
- p95 latency
- Pod restarts
- CPU usage
- Memory usage

## CI and Image Delivery Flow

```text
git push to main
   |
   v
GitHub Actions
   |-- test
   |-- changes detect
   |-- k8s-validate
   |-- docker-build-push (conditional)
   v
Amazon ECR
```

`docker-build-push` only runs when Docker image inputs change:

- `app/**`
- `Dockerfile`
- `.dockerignore`

This keeps README, workflow, and Kubernetes-only edits from creating unnecessary ECR images.

## Architecture Decisions

### EKS Instead of kind

I used Amazon EKS because this lab is meant to demonstrate cloud SRE workflows, not only local Kubernetes syntax. `kind` is useful for fast local iteration, but it hides several operational concerns that matter in real environments:

- Cloud IAM and AWS credentials
- ECR image pull behavior
- Managed node groups
- AWS cleanup and orphan resource checks
- Real cloud cost tradeoffs

The tradeoff is cost and setup time. EKS is slower and more expensive than `kind`, so the cluster is treated as ephemeral: create it for deployment, monitoring, and screenshots, then delete it after the lab evidence is captured.

### Two `t3.small` Worker Nodes

The lab used two `t3.small` worker nodes because the original `t3.medium` plan was not available under the account's free-plan constraints. Two smaller nodes still demonstrate the core Kubernetes scheduling model better than a single node:

- The app runs with `replicas: 2`
- Pods can be scheduled across more than one worker
- The monitoring stack has room to run alongside the app
- Node and pod screenshots show a realistic multi-node cluster shape

This is not a production sizing recommendation. It is a cost-aware lab configuration that balances AWS limits, observability workload requirements, and screenshot evidence.

### `ServiceMonitor` Instead of Manual Prometheus Scrape Config

I used `ServiceMonitor` because the lab installs `kube-prometheus-stack`, which includes the Prometheus Operator. In that setup, `ServiceMonitor` is the Kubernetes-native way to declare scrape targets.

Why this is better than hand-editing Prometheus scrape config:

- Scrape configuration lives in Kubernetes manifests and can be versioned with the app.
- Prometheus discovers targets by labels instead of hardcoded Pod IPs.
- The config survives Pod rescheduling because the Service remains stable.
- It matches how Prometheus Operator is commonly used in Kubernetes environments.

The important relationship is:

```text
ServiceMonitor selects Service: sre-app
Prometheus pulls /metrics from the discovered endpoints
FastAPI exposes metrics at /metrics
```

The app does not push metrics to Prometheus. Prometheus owns the scrape loop.

### ECR Image Tags: Git SHA and `latest`

The CI pipeline pushes two tags for each image build:

- Git SHA tag: immutable reference for traceability
- `latest`: convenient rolling tag for quick manual testing

For production deployments, the Git SHA tag is safer because it answers exactly which commit produced the running image. `latest` is convenient but ambiguous.

### Conditional Docker Build in CI

Docker image builds only run when image inputs change:

- `app/**`
- `Dockerfile`
- `.dockerignore`

This prevents README, architecture docs, workflow-only edits, and Kubernetes-only edits from creating unnecessary ECR images. Tests and manifest validation still run on normal pushes, but image delivery is reserved for changes that can actually affect the container.

### CI + Artifact Delivery, Not Full CD

This project intentionally stops at image delivery:

```text
git push -> CI checks -> build image -> push ECR
```

Full CD would update the EKS deployment after publishing the image:

```text
build image -> push ECR -> kubectl set image -> kubectl rollout status
```

That was kept out of scope because the cluster is deleted when not in use. Adding automatic deployment to a cluster that may not exist would make the pipeline noisier and less honest. In a production version, this would be implemented with GitHub OIDC, an IAM role, and a deployment job that uses the immutable Git SHA image tag.

