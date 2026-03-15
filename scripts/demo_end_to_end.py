"""End-to-end demo script.

This script generates an agenda (using the existing skill/LLM wiring),
writes it to `out/agenda_demo.md`, and attempts to upload to Google Drive
if credentials are provided via environment variables.

Use:
  python scripts/demo_end_to_end.py --title "April Board" --summary "Quarterly planning"

Environment variables (optional):
  GDRIVE_CREDENTIALS - path to credentials JSON (service account or client secrets)
  GDRIVE_FOLDER_ID - Drive folder id to upload into
  GDRIVE_CREDENTIAL_TYPE - 'service_account' or 'oauth' (default: service_account)
  GDRIVE_OAUTH_TOKEN - path to oauth token (optional)

The script never stores credentials in the repo and will print clear guidance
if upload is skipped.
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys

from agents.skills.president import generate_agenda_with_llm
from integrations.gdrive.drive_client import DriveClient


def run(title: str, date: str | None = None, summary: str | None = None, out_path: str | None = None) -> int:
    meeting_notes = {"title": title, "date": date or "TBD", "summary": summary or ""}
    md = generate_agenda_with_llm(meeting_notes)

    out_path = out_path or "out/agenda_demo.md"
    p = pathlib.Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(md, encoding="utf-8")
    print(f"Wrote demo agenda to {out_path}")

    creds = os.environ.get("GDRIVE_CREDENTIALS")
    folder = os.environ.get("GDRIVE_FOLDER_ID")
    ctype = os.environ.get("GDRIVE_CREDENTIAL_TYPE", "service_account")
    otoken = os.environ.get("GDRIVE_OAUTH_TOKEN")

    client = DriveClient(credentials_json=creds, folder_id=folder, credential_type=ctype, oauth_token_path=otoken)
    try:
        meta = client.upload_file(str(p), mime_type="text/markdown")
        print("Uploaded to Drive:", meta)
        return 0
    except Exception as e:
        print("Drive upload skipped or failed:", e, file=sys.stderr)
        print("To enable upload, set environment vars: GDRIVE_CREDENTIALS and GDRIVE_FOLDER_ID (or run OAuth flow).")
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="demo-e2e")
    parser.add_argument("--title", required=True)
    parser.add_argument("--date", required=False)
    parser.add_argument("--summary", required=False)
    parser.add_argument("--out", required=False)
    args = parser.parse_args(argv)
    return run(args.title, args.date, args.summary, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
