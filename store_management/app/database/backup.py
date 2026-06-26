import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from config import DATABASE_PATH, BACKUP_DIR


def create_backup() -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUP_DIR / f"store_backup_{stamp}.db"
    src_conn = sqlite3.connect(str(DATABASE_PATH))
    dst_conn = sqlite3.connect(str(dest))
    src_conn.backup(dst_conn)
    src_conn.close()
    dst_conn.close()
    _cleanup_old_backups()
    return dest


def _cleanup_old_backups(keep: int = 30):
    backups = sorted(BACKUP_DIR.glob("store_backup_*.db"), key=lambda p: p.stat().st_mtime)
    for old in backups[:-keep]:
        old.unlink(missing_ok=True)


def list_backups() -> list[dict]:
    return [
        {"name": p.name, "path": str(p), "size": p.stat().st_size, "date": datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y %H:%M")}
        for p in sorted(BACKUP_DIR.glob("store_backup_*.db"), reverse=True)
    ]


def restore_backup(backup_path: str):
    src = Path(backup_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")
    shutil.copy2(src, DATABASE_PATH)
