# TODOs

Currently undergoing a major refactor. The goal is to create a modular, production-grade, distributed ci/cd system and decided to track the state of TODOs here.

- [ ] Refactors
	- [ ] Extend the API architecture with a dedicated control plane
        - [ ] Decouple agent and rebuilder from API
        - [ ] Revisit Rebuilder design 
	- [ ] Replace in memory queue with distributed message queue
	- [ ] Move builder services back into api layer
    - [ ] Artifactstore become proper service
- [x] Create devcontainer
	- [x] compose file that spins up postgres and a distributed mq of choice
- [ ] Testing
	- [ ] packages that need testing
		- [x] builder
	- [ ] interactions that need testing
        - [ ] job execution pipeline
- [ ] CI/CD
	- [ ] On push?
	- [ ] On merge to main?
- [ ] Versioning
- [ ] Changelogs
- [ ] Deployment
- [ ] Monitoring
- [ ] Documentation
	- [ ] Create website for documentation