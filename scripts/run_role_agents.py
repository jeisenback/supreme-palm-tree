"""Example runner for role agents.

Usage examples:
    python -m scripts.run_role_agents fundraising --csv "donor,amount\nAlice,100\nBob,50\n"
    python -m scripts.run_role_agents membership --csv-file data/members.csv
    python -m scripts.run_role_agents communications --json "{\"title\": \"Update\", \"summary\": \"News\"}"
"""

from __future__ import annotations

import sys
from agents.agents_cli import main

if __name__ == "__main__":
    # pass through CLI args to agents-cli main
    raise SystemExit(main(sys.argv[1:]))
