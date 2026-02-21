# v0.1.0
- Major refactors:
    - decoupled buildserver/agent and buildserver/api
        - both now standalone binaries
    - improved error handling in builder
    - builder now creates temporary directories when running jobs
- Known limitations:
    - No scheduler: agent must be running before jobs are dispatched, jobs enqueued while the agent is down may fail unexpectedly
    - Limited fault tolerance: no agent heartbeat or health checks, job status can become stale if the agent or API is unavailable
    - Rebuilder will not shutdown gracefully
    - All builds will fail: `make` is not installed in the runner container. This is an intentional omission — in the interest of rapid iteration, build tooling will not be added to the container as user-defined script execution is the next planned feature
# v0.0.0
- Proof of concept CI System
- Features:
    - submit jobs for execution
    - automatic rebuilds on new commits
    - creation of artifacts after successful job completion
