# Deployment Plan

## Infrastructure

### Cloud Provider
- AWS

### OS
- Amazon Linux 2023

### Kubernetes
- Self-managed cluster on EC2 instances
- 2 node setup:
  - Control plane: t3.small (2 vCPU, 2GB RAM), disk TBD
  - Worker node: t3.small (2 vCPU, 2GB RAM), disk TBD

### Containerization
- Github Registry

### Storage
