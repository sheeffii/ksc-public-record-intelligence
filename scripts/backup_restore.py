#!/usr/bin/env python3
"""Verified PostgreSQL + object-store backup and guarded restore.

Configuration is read from the same environment variables as the application.
Secret values are never written to the backup; the manifest records only which
configuration references are required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from minio import Minio


def _database_url() -> str:
    value = os.environ.get("DATABASE_URL")
    if not value:
        raise SystemExit("DATABASE_URL is required")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)


def _client() -> tuple[Minio, str]:
    endpoint = os.environ.get("MINIO_ENDPOINT")
    access = os.environ.get("MINIO_ACCESS_KEY") or os.environ.get("MINIO_ROOT_USER")
    secret = os.environ.get("MINIO_SECRET_KEY") or os.environ.get("MINIO_ROOT_PASSWORD")
    bucket = os.environ.get("MINIO_BUCKET_DOCUMENTS", "ksc-documents")
    if not endpoint or not access or not secret:
        raise SystemExit("MINIO_ENDPOINT and MinIO credentials are required")
    return (
        Minio(
            endpoint,
            access_key=access,
            secret_key=secret,
            secure=os.environ.get("MINIO_SECURE", "false").lower() == "true",
        ),
        bucket,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _executable(name: str) -> str:
    value = shutil.which(name)
    if value is None:
        raise SystemExit(f"required executable not found: {name}")
    return value


def _object_path(root: Path, object_name: str) -> Path:
    path = (root / object_name).resolve()
    if root.resolve() not in path.parents:
        raise SystemExit(f"unsafe object name in backup: {object_name}")
    return path


def backup(target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        raise SystemExit(f"backup target must be empty: {target}")
    target.mkdir(parents=True, exist_ok=True)
    database = target / "postgres.dump"
    subprocess.run(  # noqa: S603 - fixed executable and argv, no shell
        [
            _executable("pg_dump"),
            "--format=custom",
            "--no-owner",
            "--file",
            str(database),
            _database_url(),
        ],
        check=True,
    )

    client, bucket = _client()
    objects_root = target / "objects"
    files: list[dict[str, object]] = []
    for item in client.list_objects(bucket, recursive=True):
        destination = _object_path(objects_root, item.object_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.fget_object(bucket, item.object_name, str(destination))
        files.append(
            {
                "object_name": item.object_name,
                "byte_size": destination.stat().st_size,
                "sha256": _sha256(destination),
            }
        )
    manifest = {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "database": {"file": database.name, "sha256": _sha256(database)},
        "object_bucket": bucket,
        "objects": files,
        "required_configuration_references": [
            "DATABASE_URL",
            "MINIO_ENDPOINT",
            "MINIO_ACCESS_KEY/MINIO_ROOT_USER",
            "MINIO_SECRET_KEY/MINIO_ROOT_PASSWORD",
            "MINIO_BUCKET_DOCUMENTS",
        ],
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"backup verified: {len(files)} objects in {target}")


def restore(source: Path, *, confirmed: bool) -> None:
    if not confirmed:
        raise SystemExit("restore refused: pass --confirm after verifying the target environment")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    database = source / manifest["database"]["file"]
    if _sha256(database) != manifest["database"]["sha256"]:
        raise SystemExit("database backup checksum mismatch")
    for item in manifest["objects"]:
        path = _object_path(source / "objects", item["object_name"])
        if path.stat().st_size != item["byte_size"] or _sha256(path) != item["sha256"]:
            raise SystemExit(f"object backup checksum mismatch: {item['object_name']}")

    client, bucket = _client()
    if client.bucket_exists(bucket):
        if next(client.list_objects(bucket, recursive=True), None) is not None:
            raise SystemExit(f"restore object bucket must be empty: {bucket}")
    else:
        client.make_bucket(bucket)

    subprocess.run(  # noqa: S603 - fixed executable and argv, no shell
        [
            _executable("pg_restore"),
            "--clean",
            "--if-exists",
            "--no-owner",
            "--no-privileges",
            "--dbname",
            _database_url(),
            str(database),
        ],
        check=True,
    )
    for item in manifest["objects"]:
        path = _object_path(source / "objects", item["object_name"])
        client.fput_object(bucket, item["object_name"], str(path), content_type="application/pdf")
    print(f"restore verified: {len(manifest['objects'])} objects from {source}")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("path", type=Path)
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("path", type=Path)
    restore_parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if args.command == "backup":
        backup(args.path)
    else:
        restore(args.path, confirmed=args.confirm)


if __name__ == "__main__":
    main()
