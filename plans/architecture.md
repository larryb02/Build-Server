# Architecture

## Services

```
buildserver-api
buildserver-scheduler
buildserver-runner
```

### API
- Control plane for the system
- Owns runner registry and job state
- Single dispatch point for job execution
- Receives runner registrations and heartbeats

### Scheduler
- Stateless queue consumer
- Drives dispatch decisions: consumes jobs from the queue, queries the API for runner availability, and triggers dispatch
- No datastore — relies entirely on the API for state

### Runner
- Executes jobs dispatched by the API
- Registers with the API on startup
- Streams build output back to the API during job execution

## Communication

```
Queue → Scheduler → API → Runner
```

### Scheduler ↔ API (gRPC)
- Job dispatch requests
- Runner availability queries

### API ↔ Runner (gRPC)
- `RegisterAgent`: runner registers with API on startup
- `Heartbeat`: runner signals liveness
- `DispatchJob`: API sends job to runner
- Build output streaming: runner streams logs back to API during execution

## Design Principles
- API is the single control plane — scheduler and runners do not communicate directly
- Scheduler is stateless; it can be restarted or scaled without recovery concerns
