# 0.1.1
- Support for execution environments

# 0.1.0
- Replaced gRPC with REST for runner communication
- JWT-based runner authentication
- Runner registration
- Heartbeats and health checks (`last_seen`, `health` fields)
- Removed RabbitMQ dependency
- Fixed bug where builder starts in wrong working directory
- Status updates sent throughout build job
- Pipeline support
- Runner auth hardening

# 0.0.2
- Enforce HTTPS for git repository URLs
- Runner now supports user-defined script execution

# 0.0.1
- Script execution foundation
- Switched to dynaconf for configuration
- Centralized logging setup
