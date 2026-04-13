# Pipeline Spec (`.buildserver.yaml`)

Place a `.buildserver.yaml` file in the root of your repository. The server reads this file at trigger time by cloning the repo at the triggering commit — no other configuration is needed.

## Structure

```yaml
jobs:
  <job-name>:
    run: <shell command>
```

## Top-level keys

| Key | Required | Description |
|-----|----------|-------------|
| `jobs` | yes | Map of named jobs to run as part of this pipeline |

## Job

Each key under `jobs` is the job name. Jobs are dispatched as independent units of work to available runners. Each job has exactly one `run` entry.

| Key | Required | Description |
|-----|----------|-------------|
| `run` | yes | Shell command to execute for this job |

## Execution model

- **Jobs run in parallel** (when multiple runners are available) — do not assume ordering between jobs.
- The spec is read at trigger time. Changes to `.buildserver.yaml` take effect on the next trigger.
- The command is executed as-is in a shell on the runner host.

## Example

```yaml
jobs:
  build:
    run: pip install -r requirements.txt && python -m py_compile src/main.py

  test:
    run: pytest tests/ -v

  package:
    run: tar -czf dist/app.tar.gz src/
```
