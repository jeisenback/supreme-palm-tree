"""Simple CLI for agents tasks (PoC).

Commands:
- ingest --src PATH [--out OUT_DIR]

This module is intentionally small and synchronous; it's designed as an
administrative CLI to invoke the existing `ingest` pipeline.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from ingest.converters import convert_file_to_md_context
from ingest.storage import store_conversion
from agents.skills.president import generate_agenda_with_llm
from agents.skills import (
    generate_fundraising_plan,
    generate_membership_insights,
    draft_announcement,
    generate_email_campaign,
)
from integrations.gdrive.drive_client import DriveClient
import json
from agents import scheduler
from ingest.scrapers import approvals


def cmd_ingest(src: str, out_dir: Optional[str] = None) -> int:
    """Ingest a single source file and store the conversion using existing pipeline.

    Returns exit code 0 on success, non-zero on failure.
    """
    try:
        md_text, context, assets = convert_file_to_md_context(src)
        out_path, json_path = store_conversion(md_text, context, assets, src, out_dir or "out")
        print(f"Ingested {src} -> {out_path} (context: {json_path})")
        return 0
    except Exception as e:
        print(f"Error ingesting {src}: {e}", file=sys.stderr)
        return 2


def cmd_approve_add(source_id: str, meta: Optional[str] = None) -> int:
    try:
        metadata = None
        if meta:
            metadata = json.loads(meta)
        approvals.approve_source(source_id, metadata)
        print(f"Approved source: {source_id}")
        return 0
    except Exception as e:
        print(f"Failed to approve source {source_id}: {e}", file=sys.stderr)
        return 10


def cmd_approve_revoke(source_id: str) -> int:
    try:
        approvals.revoke_source(source_id)
        print(f"Revoked approval: {source_id}")
        return 0
    except Exception as e:
        print(f"Failed to revoke source {source_id}: {e}", file=sys.stderr)
        return 11


def cmd_approve_list() -> int:
    try:
        items = approvals.list_approved()
        if not items:
            print("No approved sources found.")
            return 0
        for it in items:
            print(json.dumps(it, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"Failed to list approvals: {e}", file=sys.stderr)
        return 12


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="agents-cli")
    sub = parser.add_subparsers(dest="cmd")

    p_ingest = sub.add_parser("ingest", help="Ingest a file via the ingest pipeline")
    p_ingest.add_argument("--src", required=True, help="Path to source file to ingest")
    p_ingest.add_argument("--out", required=False, help="Output directory (default: out)")

    p_drive = sub.add_parser("drive", help="Drive export commands")
    p_drive_sub = p_drive.add_subparsers(dest="drive_cmd")

    p_drive_agenda = p_drive_sub.add_parser("export-agenda", help="Generate an agenda and upload to Drive")
    p_drive_agenda.add_argument("--title", required=True, help="Agenda title")
    p_drive_agenda.add_argument("--date", required=False, help="Agenda date")
    p_drive_agenda.add_argument("--summary", required=False, help="Brief summary for agenda")
    p_drive_agenda.add_argument("--out", required=False, help="Local output path for markdown (default: out/agenda.md)")
    p_drive_agenda.add_argument("--drive-folder", required=False, help="Drive folder id to upload into")
    p_drive_agenda.add_argument("--credentials", required=False, help="Path to credentials JSON (service account or client secrets)")
    p_drive_agenda.add_argument("--credential-type", required=False, choices=["service_account","oauth"], default="service_account")
    p_drive_agenda.add_argument("--oauth-token", required=False, help="Path to oauth token (if using oauth credential_type)")

    p_sched = sub.add_parser("scheduler", help="Scheduler control commands")
    p_sched_sub = p_sched.add_subparsers(dest="sched_cmd")

    p_sched_sub.add_parser("start", help="Start the background scheduler")
    p_sched_sub.add_parser("stop", help="Stop the background scheduler")
    p_sched_sub.add_parser("run-once", help="Run each registered job once synchronously")
    p_watch = sub.add_parser("watch", help="Start folder watcher to trigger ingestion on new files")
    p_watch.add_argument("--path", required=True, help="Directory to watch")
    p_watch.add_argument("--background", action="store_true", help="Run watcher in background (default behavior for CLI is to run until Ctrl-C)")

    p_watch_drive = sub.add_parser("watch-drive", help="Watch a Google Drive folder for new files (downloads and processes transcripts)")
    p_watch_drive.add_argument("--folder-id", required=True, help="Drive folder id to watch")
    p_watch_drive.add_argument("--interval", required=False, type=int, default=30, help="Poll interval seconds (default: 30)")
    p_watch_drive.add_argument("--credentials", required=False, help="Path to credentials JSON (service account or client secrets)")
    p_watch_drive.add_argument("--credential-type", required=False, choices=["service_account", "oauth"], default="service_account")
    p_watch_drive.add_argument("--oauth-token", required=False, help="Path to oauth token (if using oauth credential_type)")
    p_watch_drive.add_argument("--state-path", required=False, help="Path to persist seen Drive file ids (default: out/drive_seen.json)")

    p_approve = sub.add_parser("approve", help="Manage approvals for scraper sources")
    p_approve_sub = p_approve.add_subparsers(dest="approve_cmd")

    p_approve_add = p_approve_sub.add_parser("add", help="Approve a source id for scraping")
    p_approve_add.add_argument("source_id", help="Unique source id to approve")
    p_approve_add.add_argument("--meta", required=False, help="Optional JSON metadata for the source")

    p_approve_revoke = p_approve_sub.add_parser("revoke", help="Revoke an approved source")
    p_approve_revoke.add_argument("source_id", help="Unique source id to revoke")

    p_approve_list = p_approve_sub.add_parser("list", help="List approved sources")

    p_weekly = sub.add_parser("weekly-update", help="Generate weekly board update from notes")
    p_weekly_sub = p_weekly.add_subparsers(dest="weekly_cmd")

    p_weekly_generate = p_weekly_sub.add_parser("generate", help="Generate a draft weekly update (requires publish to send)")
    p_weekly_generate.add_argument("--title", required=False, help="Update title (default: Weekly Board Update)")
    p_weekly_generate.add_argument("--out", required=False, help="Output markdown path (if saving outside pending)")
    p_weekly_generate.add_argument("--no-llm", action="store_true", help="Do not use LLM for summarization")

    p_weekly_list = p_weekly_sub.add_parser("list-pending", help="List pending drafts awaiting review")

    p_weekly_publish = p_weekly_sub.add_parser("publish", help="Publish a pending draft (human approval)")
    p_weekly_publish.add_argument("id", help="ID of the pending draft to publish")
    p_weekly_publish.add_argument("--drive-folder", required=False, help="Drive folder id to upload published update into")
    p_weekly_publish.add_argument("--credentials", required=False, help="Path to credentials JSON (service account or client secrets)")
    p_weekly_publish.add_argument("--credential-type", required=False, choices=["service_account", "oauth"], default="service_account")
    p_weekly_publish.add_argument("--oauth-token", required=False, help="Path to oauth token (if using oauth credential_type)")

    # Role agents: fundraising, membership, communications
    p_role = sub.add_parser("role", help="Invoke role agents (fundraising, membership, communications)")
    p_role_sub = p_role.add_subparsers(dest="role_cmd")

    p_role_fund = p_role_sub.add_parser("fundraising", help="Run fundraising role agent on CSV input")
    p_role_fund.add_argument("--csv", required=False, help="CSV text inline")
    p_role_fund.add_argument("--csv-file", required=False, help="Path to CSV file")

    p_role_mem = p_role_sub.add_parser("membership", help="Run membership role agent on CSV input")
    p_role_mem.add_argument("--csv", required=False, help="CSV text inline")
    p_role_mem.add_argument("--csv-file", required=False, help="Path to CSV file")

    p_role_comm = p_role_sub.add_parser("communications", help="Run communications agent to draft announcement")
    p_role_comm.add_argument("--json", required=False, help="JSON string for context")
    p_role_comm.add_argument("--json-file", required=False, help="Path to JSON file for context")
    p_role_comm.add_argument("--subject", required=False, help="Subject for email campaign (communications only)")
    p_role_comm.add_argument("--audience", required=False, help="Audience summary for email campaign")

    args = parser.parse_args(argv)
    if args.cmd == "ingest":
        return cmd_ingest(args.src, args.out)
    if args.cmd == "drive":
        if args.drive_cmd == "export-agenda":
            title = args.title
            date = args.date or "TBD"
            summary = args.summary or ""
            out_path = args.out or "out/agenda.md"
            folder = args.drive_folder
            creds = args.credentials
            credential_type = args.credential_type
            oauth_token = args.oauth_token

            # generate agenda (LLM used if available)
            meeting_notes = {"title": title, "date": date, "summary": summary}
            md = generate_agenda_with_llm(meeting_notes)

            # ensure output dir exists and write markdown
            import pathlib
            p = pathlib.Path(out_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(md, encoding="utf-8")
            print(f"Wrote agenda to {out_path}")

            # attempt upload
            client = DriveClient(credentials_json=creds, folder_id=folder, credential_type=credential_type, oauth_token_path=oauth_token)
            try:
                meta = client.upload_file(str(p), mime_type="text/markdown")
                print(f"Uploaded to Drive: {meta}")
                return 0
            except Exception as e:
                print(f"Drive upload failed: {e}", file=sys.stderr)
                return 3
    if args.cmd == "scheduler":
        if args.sched_cmd == "start":
            try:
                scheduler.register_default_jobs()
                scheduler.start()
                print("Scheduler started (background).")
                return 0
            except Exception as e:
                print(f"Failed to start scheduler: {e}", file=sys.stderr)
                return 4
        if args.sched_cmd == "stop":
            try:
                scheduler.stop()
                print("Scheduler stopped.")
                return 0
            except Exception as e:
                print(f"Failed to stop scheduler: {e}", file=sys.stderr)
                return 5
        if args.sched_cmd == "run-once":
            try:
                scheduler.register_default_jobs()
                scheduler.run_once()
                print("Ran registered jobs once.")
                return 0
            except Exception as e:
                print(f"Failed to run jobs once: {e}", file=sys.stderr)
                return 6
    if args.cmd == "watch":
        from agents.watcher import start_watcher

        def _on_new_file(path: str) -> None:
            print(f"Detected new file: {path}")
            # best-effort ingestion; we ignore return codes here
            try:
                cmd_ingest(path)
            except Exception as e:
                print(f"Watcher ingestion failed for {path}: {e}")

        try:
            thread = start_watcher(args.path, _on_new_file, background=args.background)
            if args.background:
                print("Watcher started in background.")
                return 0
            else:
                print("Watcher running. Press Ctrl-C to stop.")
                try:
                    while True:
                        import time

                        time.sleep(1)
                except KeyboardInterrupt:
                    print("Stopping watcher...")
                    # best-effort stop for observer if provided
                    try:
                        if hasattr(thread, "stop"):
                            thread.stop()
                        if hasattr(thread, "join"):
                            thread.join(timeout=2.0)
                    except Exception:
                        pass
                    return 0
        except Exception as e:
            print(f"Failed to start watcher: {e}", file=sys.stderr)
            return 7
    if args.cmd == "watch-drive":
        from agents.watcher import start_drive_watcher
        from agents.transcript_processor import process_transcript_file

        folder = args.folder_id
        interval = args.interval
        creds = getattr(args, "credentials", None)
        credential_type = getattr(args, "credential_type", "service_account")
        oauth_token = getattr(args, "oauth_token", None)

        def _on_new(file_path: str) -> None:
            print(f"Drive watcher detected new file: {file_path}")
            try:
                outp = process_transcript_file(file_path, out_dir="out/transcripts", use_llm=True)
                print(f"Processed transcript -> {outp}")
            except Exception as e:
                print(f"Failed to process transcript {file_path}: {e}", file=sys.stderr)

        try:
            thread = start_drive_watcher(folder, _on_new, poll_interval=interval, credentials_json=creds, credential_type=credential_type, oauth_token_path=oauth_token)
            print("Drive watcher started. Press Ctrl-C to stop.")
            try:
                while True:
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping drive watcher...")
                return 0
        except Exception as e:
            print(f"Failed to start drive watcher: {e}", file=sys.stderr)
            return 8

    if args.cmd == "approve":
        if args.approve_cmd == "add":
            return cmd_approve_add(args.source_id, getattr(args, "meta", None))
        if args.approve_cmd == "revoke":
            return cmd_approve_revoke(args.source_id)
        if args.approve_cmd == "list":
            return cmd_approve_list()
    if args.cmd == "weekly-update":
        from agents.weekly_update import create_draft, list_pending, publish_update

        if args.weekly_cmd == "generate":
            title = args.title or "Weekly Board Update"
            use_llm = not getattr(args, "no_llm", False)
            try:
                meta = create_draft(title=title, notes_dir="notes", use_llm=use_llm)
                print(f"Draft created: id={meta['id']} path={meta['path']}")
                print("Run 'agents-cli weekly-update list-pending' to view drafts, and 'agents-cli weekly-update publish <id>' to publish.")
                return 0
            except Exception as e:
                print(f"Failed to create draft: {e}", file=sys.stderr)
                return 21
        if args.weekly_cmd == "list-pending":
            try:
                items = list_pending()
                if not items:
                    print("No pending drafts.")
                    return 0
                import json

                for it in items:
                    print(json.dumps(it, ensure_ascii=False))
                return 0
            except Exception as e:
                print(f"Failed to list pending drafts: {e}", file=sys.stderr)
                return 22
        if args.weekly_cmd == "publish":
            uid = args.id
            drive_folder = getattr(args, "drive_folder", None)
            creds = getattr(args, "credentials", None)
            credential_type = getattr(args, "credential_type", "service_account")
            oauth_token = getattr(args, "oauth_token", None)
            try:
                dest = publish_update(uid, drive_folder=drive_folder, credentials_json=creds, credential_type=credential_type, oauth_token_path=oauth_token)
                if not dest:
                    print(f"No pending draft with id {uid} found.")
                    return 23
                print(f"Published draft to {dest}")
                return 0
            except Exception as e:
                print(f"Failed to publish draft {uid}: {e}", file=sys.stderr)
                return 24

    # Role command handlers
    if args.cmd == "role":
        # Fundraising
        if args.role_cmd == "fundraising":
            csv_text = None
            if getattr(args, "csv", None):
                csv_text = args.csv
            elif getattr(args, "csv_file", None):
                import pathlib

                p = pathlib.Path(args.csv_file)
                csv_text = p.read_text(encoding="utf-8")
            else:
                print("Provide --csv or --csv-file", file=sys.stderr)
                return 30
            try:
                out = generate_fundraising_plan(csv_text)
                print(out)
                return 0
            except Exception as e:
                print(f"Fundraising agent failed: {e}", file=sys.stderr)
                return 31

        # Membership
        if args.role_cmd == "membership":
            csv_text = None
            if getattr(args, "csv", None):
                csv_text = args.csv
            elif getattr(args, "csv_file", None):
                import pathlib

                p = pathlib.Path(args.csv_file)
                csv_text = p.read_text(encoding="utf-8")
            else:
                print("Provide --csv or --csv-file", file=sys.stderr)
                return 32
            try:
                out = generate_membership_insights(csv_text)
                print(out)
                return 0
            except Exception as e:
                print(f"Membership agent failed: {e}", file=sys.stderr)
                return 33

        # Communications
        if args.role_cmd == "communications":
            ctx = None
            if getattr(args, "json", None):
                import json

                ctx = json.loads(args.json)
            elif getattr(args, "json_file", None):
                import pathlib, json

                p = pathlib.Path(args.json_file)
                ctx = json.loads(p.read_text(encoding="utf-8"))
            else:
                print("Provide --json or --json-file", file=sys.stderr)
                return 34

            # If subject+audience provided, produce an email campaign
            if getattr(args, "subject", None) and getattr(args, "audience", None):
                try:
                    camp = generate_email_campaign(args.subject, args.audience)
                    import json

                    print(json.dumps(camp, ensure_ascii=False, indent=2))
                    return 0
                except Exception as e:
                    print(f"Communications email campaign failed: {e}", file=sys.stderr)
                    return 35
            # Otherwise draft announcement
            try:
                out = draft_announcement(ctx)
                print(out)
                return 0
            except Exception as e:
                print(f"Communications draft failed: {e}", file=sys.stderr)
                return 36

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
