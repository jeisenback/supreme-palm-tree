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
from integrations.gdrive.drive_client import DriveClient
import json
from agents import scheduler


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

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
