## (pre 1.0.0)
- [ ] Builder isolation abstraction
	- [ ] Introduce a base `Builder` class and a `ShellBuilder` subclass
		- `ShellBuilder` bootstraps the execution environment (e.g. sets up cwd, permissions, env vars) before running the repo's build script
		- Lays groundwork for future executor types
- [ ] YAML spec

## General
- [ ] Refactors
	- [ ] Config: support ENV variables with CLI arg overrides (remove .env file dependency)
	- [ ] Standardize jobs service return types (some return raw rows, some return `JobRead` models)
		- Convert SQL queries over to ORM style
		- Revisit all sql queries using 1.0 style and execute()
	- [ ] Tests
		- [ ] Add `db_session_ctx` fixture to conftest
	- [ ] Rebuilder
		- [ ] Webhook support (pre-1.0): receive push events from VCS platforms instead of polling
			- [ ] Auto-register webhooks via API (e.g. GitHub POST /repos/{owner}/{repo}/hooks) on job registration
			- [ ] Requires user token with admin:repo_hook scope
	- [ ] Replace jwts with opaque access tokens
