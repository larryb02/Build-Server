# v0.1.0
- Major refactors:
    - decoupled buildserver/agent and buildserver/api
        - both now standalone binaries
    - improved error handling in builder
    - builder now creates temporary directories when running jobs
# v0.0.0
- Proof of concept CI System
- Features:
    - submit jobs for execution
    - automatic rebuilds on new commits
    - creation of artifacts after successful job completion
