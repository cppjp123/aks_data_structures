
# Cloud-Native Data Structures Platform on AWS

## Project Overview

This project demonstrates a full, production-oriented DevOps workflow for deploying and operating a cloud-native application on AWS using Kubernetes.  
The application exposes basic data structure implementations as independent microservices and focuses on automation, scalability, and observability.

The system is deployed using Infrastructure as Code, managed through CI/CD pipelines, configured via Helm, and monitored using Prometheus and Grafana.

---

## Architecture Summary

### Backend Microservices

The backend consists of three independent microservices, each implemented in a different programming language:

- **Stack Service** – C  
- **Linked List Service** – Java  
- **Tree Service** – Python  

Each service:
- Runs in its own Docker container
- Exposes a REST API
- Is deployed as a Kubernetes Deployment with two replicas
- Communicates internally using Kubernetes Services

### Backend Aggregation Layer

A central backend application (`app.py`) acts as an API aggregation layer:
- Receives requests from the frontend
- Routes requests to the appropriate microservice
- Aggregates responses when needed
- Exposes a single entry point to the UI

### Frontend

The frontend is a lightweight web UI that:
- Communicates only with the backend API
- Displays data structure operation results
- Provides a simple visual interface

### Database

- PostgreSQL is used for persistence
- Stores execution results and metadata
- Deployed inside the Kubernetes cluster

---

## Local Development

- The full system is implemented locally using **Minikube**
- A custom `manager.py` script orchestrates service startup
- This setup serves as the baseline before cloud deployment

---

## AWS Deployment

### Infrastructure as Code (Terraform)

All AWS resources are provisioned using Terraform, including:
- VPC and networking
- Subnets and routing
- Security groups
- IAM roles and policies
- EC2 instance hosting Kubernetes

The initial deployment targets a single EC2 instance for simplicity, with a scalable design.

### Kubernetes

Kubernetes is responsible for:
- Container orchestration
- Service discovery
- Scaling and health management

Each component is deployed as:
- Deployment (2 replicas)
- Service for internal communication

---

## CI/CD Pipeline (Jenkins)

### Repositories

- Frontend repository
- Backend repository
- DevOps repository (Terraform, Helm charts, Jenkins pipelines)

### Pipeline Stages

1. Source code checkout
2. Unit testing (before merge)
3. Docker image build
4. Image push to registry
5. Deployment using Helm
6. Post-deployment validation

Pipelines are triggered automatically via GitHub webhooks.

---

## Monitoring and Observability

### Metrics

Backend services expose metrics in Prometheus format, including:
- Request count
- Request latency
- Error rate
- Service availability

### Prometheus

Prometheus is used to:
- Scrape metrics from Kubernetes pods
- Store time-series data
- Provide visibility into system health

### Grafana

Grafana visualizes Prometheus metrics.

Example dashboards:
- Application performance (latency, errors, throughput)
- Kubernetes and infrastructure health (CPU, memory, pod status)

---

## Helm Usage

### What Helm Is

Helm is a package manager for Kubernetes.  
It groups multiple Kubernetes YAML templates into a single deployable unit called a **Helm chart**.

Helm:
- Uses templates for Kubernetes resources
- Injects configuration using values files
- Generates and applies final Kubernetes YAML automatically

Helm does not replace Kubernetes YAML — it manages and controls it.

### How Helm Fits This Project

- Each service still has its own Deployment and Service templates
- Helm controls configuration such as replicas, environment name, and feature flags
- Jenkins uses Helm to deploy applications consistently across environments

---

## Basic Helm Examples

### 1. Environment Awareness

Helm controls which environment the application is running in.

UI Example:
```
Data Structures Platform
Environment: DEV
```

The same application can show:
```
Environment: PROD
```

This is achieved by changing Helm values, not code.

### 2. Scaling via Configuration

Helm controls replica counts.

UI Example:
```
Stack Service
Replicas: 2
```

After scaling:
```
Replicas: 4
```

Scaling is handled through configuration, not application changes.

### 3. Feature Toggles

Helm enables or disables features per environment.

Feature disabled:
```
Database Info: Hidden
```

Feature enabled:
```
Database Info: Connected
```

This allows safe feature control across environments.

---

## End-to-End DevOps Flow

```
Developer → GitHub → Jenkins → Helm → Kubernetes → Running Application
```

---

## Outcome

This project demonstrates:
- Infrastructure as Code with Terraform
- Microservices deployed on Kubernetes
- CI/CD automation with Jenkins
- Configuration management with Helm
- Monitoring and observability with Prometheus and Grafana

It reflects real-world DevOps engineering practices and provides a clear, maintainable, and scalable deployment model.
