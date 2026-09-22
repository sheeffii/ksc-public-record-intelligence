#!/usr/bin/env python3
"""Combine tracked corpus manifests into one pinned corpus manifest.

The Phase 10-12 quality gates take a corpus manifest as their pinned input
(which held versions are approved sources). After Phase 13 the held corpus is
the union of several capture bundles, so the gates need one manifest that
lists every verified record of every bundle. Records are concatenated in
bundle order, counts are recomputed, uniqueness of version references and
hashes is enforced by the manifest model, and refused records are carried
over so the file still documents every bundle in full.

    .venv/bin/python scripts/combine_corpus_manifests.py \\
        docs/ingestion/manifests/phase7-controlled-corpus.json \\
        docs/ingestion/manifests/phase13-corpus-02.json \\
        --out docs/ingestion/manifests/phase13-controlled-corpus.json
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from ksc_ingestion.corpus_manifest import (
    CorpusManifest,
    validate_manifest_file,
    write_manifest,
)


def combine(paths: list[Path]) -> CorpusManifest:
    parts = [validate_manifest_file(path) for path in paths]
    cases = {part.case_number for part in parts}
    if len(cases) != 1:
        raise ValueError(f"manifests describe different cases: {sorted(cases)}")
    records = [record for part in parts for record in part.records]
    refused = [item for part in parts for item in part.refused]
    return CorpusManifest(
        schema_version=parts[0].schema_version,
        case_number=parts[0].case_number,
        bundle_id="+".join(part.bundle_id for part in parts),
        generated_at=datetime.now(UTC),
        source="union of the tracked per-bundle corpus manifests: "
        + ", ".join(p.name for p in paths),
        note=(
            "Metadata only; every record was verified by its bundle's quality gate. "
            "PDFs live in object storage under object_key and are identified by sha256."
        ),
        record_count=len(records),
        document_count=len({r.document_official_ref for r in records}),
        version_count=len({r.official_version_ref for r in records}),
        total_bytes=sum(r.byte_size for r in records),
        records=records,
        refused=refused,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("manifests", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    manifest = combine(args.manifests)
    write_manifest(manifest, args.out)
    validate_manifest_file(args.out)
    print(
        f"wrote {args.out}: {manifest.record_count} records, {manifest.document_count} documents, "
        f"{manifest.version_count} versions, {manifest.total_bytes:,} bytes, "
        f"{len(manifest.refused)} refused"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
