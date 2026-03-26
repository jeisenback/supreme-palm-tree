"""Drive examples: listing, downloading, and uploading using DriveClient.

Usage:
  python scripts/drive_examples.py list --credentials /path/sa.json --folder 1AbCd
  python scripts/drive_examples.py download --file-id FILEID --credentials /path/sa.json
  python scripts/drive_examples.py upload --path mydoc.md --credentials /path/sa.json --folder 1AbCd
"""
from __future__ import annotations

import argparse
import sys
from integrations.gdrive.drive_client import DriveClient


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drive-examples")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list")
    p_list.add_argument("--credentials", required=True)
    p_list.add_argument("--folder", required=False)

    p_download = sub.add_parser("download")
    p_download.add_argument("--credentials", required=True)
    p_download.add_argument("--file-id", required=True)
    p_download.add_argument("--out", required=False, default="./downloaded")

    p_upload = sub.add_parser("upload")
    p_upload.add_argument("--credentials", required=True)
    p_upload.add_argument("--path", required=True)
    p_upload.add_argument("--folder", required=False)

    args = parser.parse_args(argv)
    if args.cmd == "list":
        client = DriveClient(credentials_json=args.credentials, folder_id=args.folder)
        files = client.list_files(folder_id=args.folder)
        for f in files:
            print(f)
        return 0
    if args.cmd == "download":
        client = DriveClient(credentials_json=args.credentials)
        out_path = args.out
        client.download_file(args.file_id, out_path)
        print("Downloaded to", out_path)
        return 0
    if args.cmd == "upload":
        client = DriveClient(credentials_json=args.credentials, folder_id=args.folder)
        meta = client.upload_file(args.path)
        print("Uploaded:", meta)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
