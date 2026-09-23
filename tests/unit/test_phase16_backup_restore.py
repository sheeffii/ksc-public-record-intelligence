from __future__ import annotations

from pathlib import Path

import pytest
from scripts import backup_restore


def test_restore_refuses_nonempty_database_before_object_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "backup"
    source.mkdir()
    database = source / "postgres.dump"
    database.write_bytes(b"dump")
    (source / "manifest.json").write_text(
        '{"database":{"file":"postgres.dump","sha256":"'
        + backup_restore._sha256(database)
        + '"},"objects":[]}',
        encoding="utf-8",
    )
    monkeypatch.setattr(
        backup_restore,
        "_assert_empty_restore_database",
        lambda: (_ for _ in ()).throw(SystemExit("restore database must be empty")),
    )
    monkeypatch.setattr(
        backup_restore,
        "_client",
        lambda: (_ for _ in ()).throw(AssertionError("object storage must not be touched")),
    )

    with pytest.raises(SystemExit, match="restore database must be empty"):
        backup_restore.restore(source, confirmed=True)
