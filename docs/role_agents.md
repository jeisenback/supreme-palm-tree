**Role Agents**

This doc shows example inputs and CLI commands for the PoC role agents included in the repository.

Example input files are in `examples/role_agents/`.

Quick commands (run from repository root):

- Fundraising (from example CSV):

  PYTHONPATH=. python -m agents.agents_cli role fundraising --csv-file examples/role_agents/donors.csv

- Membership insights:

  PYTHONPATH=. python -m agents.agents_cli role membership --csv-file examples/role_agents/members.csv

- Communications draft / email campaign:

  PYTHONPATH=. python -m agents.agents_cli role communications --json-file examples/role_agents/ctx.json

- Professional Development:

  PYTHONPATH=. python -m agents.agents_cli role professional_development --json-file examples/role_agents/skills.json

- Operations checklist:

  PYTHONPATH=. python -m agents.agents_cli role operations --json-file examples/role_agents/ops.json

- Accelerator plan:

  PYTHONPATH=. python -m agents.agents_cli role accelerator --json-file examples/role_agents/apps.json

Notes:
- These agents are PoC implementations intended for local experimentation. Use the `--csv` and `--json` flags to pass inline data when convenient.
- When running in CI or automation, set `PYTHONPATH=.` so the package imports resolve correctly.
