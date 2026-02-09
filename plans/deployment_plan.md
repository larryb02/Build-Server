# Deployment Plan

## Infrastructure

### Cloud Provider
- AWS

### OS
- CentOS Stream 9

### Kubernetes
- Self-managed cluster on EC2 instances
- 2 node setup:
  - Control plane: t3.small (2 vCPU, 2GB RAM), disk TBD
  - Worker node: t3.small (2 vCPU, 2GB RAM), disk TBD
- Estimated cost: ~$30/month on-demand (2x t3.small), less with reserved/spot

### IaC
- Terraform
  - Provisioning EC2 instances
  - Deploying Kubernetes clusters
  - Networking (VPC, security groups, etc.)

### Containerization
- Github Registry

### Storage

### Ansible
- Configuration management for EC2 instances post-provisioning
  - Container runtime installation
  - Kubernetes bootstrap (kubeadm)
  - System packages and dependencies
  - OS hardening
