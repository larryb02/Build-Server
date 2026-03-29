# Architecture

## Overview

``` mermaid
graph LR
    Client([Client]) -->|REST| API

    subgraph Control Plane
        API[APIServer]
    end

    API -->|read/write| PostgreSQL[(PostgreSQL)]

    subgraph Runner
        Agent[Agent]
        Builder[Builder]
    end

    Agent -->|poll for jobs| API
    Agent --> Builder
    Agent -->|status updates| API
```

## Job Lifecycle

``` mermaid
sequenceDiagram
    participant C as Client
    participant A as API
    participant R as Runner Agent
    participant G as Git Remote

    C->>A: POST /api/v1/jobs
    A->>A: Create job record (QUEUED)
    A->>C: 200 OK (job metadata)

    loop Poll for work
        R->>A: POST /api/v1/jobs/request
        A->>R: Job payload (or empty)
    end

    R->>A: PATCH /api/v1/jobs/{id} (RUNNING)
    R->>G: Clone repository
    R->>R: Execute job
    alt Build succeeds
        R->>A: PATCH /api/v1/jobs/{id} (SUCCEEDED)
    else Build fails
        R->>A: PATCH /api/v1/jobs/{id} (FAILED)
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
