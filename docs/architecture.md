# Architecture

## API
REST API that exposes an interface for a client to communicate with the build server system.

Built using FastAPI framework.

## Build Agent
Long running process that consumes jobs from a message queue and executes builds.

The build agent:

- Maintains connection to RabbitMQ
- Executes build jobs in isolated temp directories
- Reports status back to API via HTTP

## Builder
Handles cloning repositories and running build commands.

## Rebuilder
Background task that checks for new commits for any builds known to the server.

## Artifact Repository
Structured directory that stores artifacts with the following pattern: `<commit_hash>/artifact`

Ideally the artifact repository should be able to exist locally, on a file server, or on a cloud based object store such as Amazon S3 (WIP).

## Database
PostgreSQL server with tables:

- **Job** - Stores metadata about jobs such as status, repository URL, and commit hash
- **Artifact** - Stores metadata about artifacts such as the artifact's path in the repository
