# Python environments, dependencies, and runtime configuration

Python projects are easier to maintain when four separate concerns remain separate:

| Concern | Purpose | Typical artifact |
| --- | --- | --- |
| Python environment | Isolates installed packages | `.venv/` |
| Dependency declaration | States what the project needs | `pyproject.toml` |
| Dependency resolution | Pins a reproducible package graph | `uv.lock` or `poetry.lock` |
| Runtime configuration and secrets | Configures an application at execution time | environment variables and local `.env` files |

The central rule is simple: **a virtual environment does not load environment variables, and a `.env` file does not install dependencies.**

## Recommended default: `uv` projects

For a new application, use `uv`, `pyproject.toml`, and `uv.lock`:

```text
pyproject.toml
    ↓ declares direct dependencies
uv.lock
    ↓ records exact resolved versions
uv sync
    ↓ creates or updates
.venv/
```

Typical workflow:

```bash
# Create a project once.
uv init

# Add a runtime dependency.
uv add fastapi

# Add a development dependency group.
uv add --group dev pytest ruff

# Create or update the local environment from the lockfile.
uv sync

# Run commands in the managed project environment.
uv run pytest
uv run ruff check .
uv run python -m my_service
```

A minimal `pyproject.toml` might look like this:

```toml
[project]
name = "my-service"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi>=0.120",
  "pydantic>=2",
]

[dependency-groups]
dev = [
  "pytest>=8",
  "ruff>=0.12",
]
```

`pyproject.toml` is the declaration of intent. `uv.lock` is the exact resolution that should be committed for an application. `.venv/` is disposable local state and should not be committed.

## Loading `.env` values with `uv`

`uv run` can load dotenv files, but environment activation alone does not. Prefer making configuration loading explicit:

```bash
uv run --env-file .env -- python -m my_service
uv run --env-file .env -- pytest
uv run --env-file .env -- uvicorn my_service.main:app --reload
```

Multiple `--env-file` options are supported; later files override earlier ones. Variables already present in the shell take precedence over values from dotenv files.

For an interactive local shell, activate the environment and then load a *trusted, shell-compatible* dotenv file:

```bash
source .venv/bin/activate
set -a
source .env
set +a
```

Do not modify `.venv/bin/activate` to load project configuration. The virtual environment can be recreated at any time, while configuration belongs to the project or deployment environment.

For automatic directory-scoped environment loading on a developer machine, `direnv` is often a better fit:

```bash
# .envrc
dotenv
```

Then run `direnv allow`. Keep `.envrc` and `.env` free of untrusted content because they are executed by the shell.

## Reading environment variables in application code

Applications should read values from the process environment. `python-dotenv` is useful when an application itself should load a local `.env` file:

```python
import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.environ["DATABASE_URL"]
debug = os.getenv("DEBUG", "false").lower() == "true"
```

Use this pattern deliberately. When `uv run --env-file .env ...`, Docker Compose, Kubernetes, or CI already injects the values, application-level dotenv loading is usually unnecessary.

Example local configuration:

```dotenv
DATABASE_URL=postgresql://localhost/mydb
DEBUG=true
API_KEY=replace-me
```

Never commit real credentials. Commit a safe template instead:

```dotenv
# .env.example
DATABASE_URL=
DEBUG=false
API_KEY=
```

## Poetry equivalent

Poetry follows the same separation of concerns, with different commands:

```text
pyproject.toml
    ↓
poetry.lock
    ↓
poetry install
    ↓
virtual environment
```

```bash
poetry add fastapi
poetry add --group dev pytest ruff
poetry install
poetry run pytest
poetry run python -m my_service
```

Poetry does not make `.env` handling identical to dependency management. Use application-level dotenv loading, an explicit shell-loading step, or a well-understood project plugin if that behavior is required.

## Traditional `venv` and `pip`

The traditional approach is still appropriate for simple projects:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
```

```text
requirements.txt
    ↓
pip install
    ↓
.venv/
```

This becomes harder to maintain when `requirements.txt` is produced with `pip freeze`: it mixes direct dependencies with transitive dependencies and makes intent difficult to see. For larger projects, prefer a declarative `pyproject.toml` plus a lockfile, or use `pip-tools` to separate input requirements from compiled pins.

## Should a project keep `requirements.txt` too?

Avoid maintaining both `pyproject.toml` and `requirements.txt` as independent sources of truth. That invites drift.

Use `requirements.txt` only when a tool or platform requires it, and generate it from the lockfile or project metadata. With `uv`, for example:

```bash
uv export --format requirements-txt --output-file requirements.txt
```

Treat the generated file as an interoperability artifact, not a second dependency definition.

## What belongs in Git?

For a typical application:

```text
pyproject.toml     commit
uv.lock            commit
.python-version    usually commit
.env.example       commit
.env               do not commit
.venv/             do not commit
__pycache__/       do not commit
```

A library may choose different lockfile policy depending on its publishing and support strategy. An application benefits from committing its lockfile because it deploys a known dependency graph.

## Development, CI, Docker, and production

Keep responsibilities distinct across environments:

```text
Developer machine
  ├── uv sync
  ├── local .env (uncommitted)
  └── uv run --env-file .env -- <command>

CI
  ├── uv sync --locked
  ├── test-specific environment variables from CI secrets
  └── uv run pytest

Container or production platform
  ├── install locked dependencies
  └── inject configuration through platform secrets/configuration
```

Do not copy a developer's `.venv/` or `.env` into a production image. Use the lockfile to build dependencies and the deployment platform's secret-management mechanism to supply credentials.

## A practical project layout

```text
my-service/
├── pyproject.toml
├── uv.lock
├── .python-version
├── .env.example
├── .gitignore
├── src/
│   └── my_service/
├── tests/
├── Dockerfile
└── README.md
```

## Decision guide

| Need | Recommended approach |
| --- | --- |
| New application or service | `uv` + `pyproject.toml` + `uv.lock` |
| Run a project command | `uv run <command>` |
| Load local dotenv values for a command | `uv run --env-file .env -- <command>` |
| Interactive local shell | `source .venv/bin/activate`, then load a trusted `.env` explicitly or use `direnv` |
| Application needs to load local dotenv itself | `python-dotenv` |
| Legacy or small pip-only project | `venv` + `pip` + `requirements.txt` |
| A system requires `requirements.txt` | Generate it; do not maintain it separately |

The useful mental model is:

```text
pyproject.toml  = what the project declares
uv.lock         = the exact resolved dependency graph
.venv/          = a disposable local installation
.env            = local runtime configuration
```

For most modern Python services, start with `uv sync` and run commands through `uv run`; load dotenv values explicitly only where they are needed.
