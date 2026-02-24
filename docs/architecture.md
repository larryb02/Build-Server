# Architecture

## Overview

``` mermaid
graph LR
    Client([Client]) -->|REST| API

    subgraph Control Plane
        API[APIServer]
        Rebuilder[Rebuilder]
    end

    API -->|publish job| RabbitMQ[(RabbitMQ)]
    API -->|read/write| PostgreSQL[(PostgreSQL)]
    Rebuilder -->API

    RabbitMQ -->|consume job| Runner

    subgraph Runner
        Agent[Agent]
        Builder[Builder]
    end

    Agent --> Builder
    Agent --> API
```

## Job Lifecycle

``` mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant Q as RabbitMQ
    participant R as Runner Agent
    participant G as Git Remote

    C->>A: POST /jobs/register
    A->>A: Create job record (QUEUED)
    A->>Q: Publish job to build_jobs queue
    A->>C: 200 OK (job metadata)

    R->>Q: Consume job
    R->>A: PATCH /jobs/{id} (RUNNING)
    R->>G: Clone repository
    R->>R: Execute build
    alt Build succeeds
        R->>A: PATCH /jobs/{id} (SUCCEEDED)
    else Build fails
        R->>A: PATCH /jobs/{id} (FAILED)
    end
```

## Components

### API
REST API that exposes an interface for a client to communicate with the build server system.

### Runner
Execution nodes responsible for consuming and running jobs from the queue.

### Rebuilder
Background task that polls for new commits on registered repositories and triggers rebuilds via the API.

!!! NOTE
    Plans to convert this into a webhook by 1.0.0

### Artifact Store
Structured directory that stores artifacts with the following pattern: `<commit_hash>/artifact`

Ideally the artifact store should be able to exist locally, on a file server, or on a cloud based object store such as Amazon S3 (WIP).

!!! NOTE
    Artifact Storage will undergo a major overhaul and will not be included in v0.1.x

### Database
PostgreSQL server with tables:

- **Job** - Stores metadata about jobs such as status, repository URL, and commit hash
- **Artifact** - Stores metadata about artifacts such as the artifact's path in the repository
