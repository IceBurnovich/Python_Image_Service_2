import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

backup_dir = Path(os.getenv("BACKUP_DIR", "backups"))
log_dir = Path(os.getenv("LOG_DIR", "logs"))
backup_dir.mkdir(parents=True, exist_ok=True)
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_dir / "app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

name = datetime.now().strftime("backup_%Y-%m-%d_%H%M%S.sql")
path = backup_dir / name
user = os.getenv("DB_USER", "postgres")
database = os.getenv("DB_NAME", "images_db")

try:
    result = subprocess.run(
        ["docker", "compose", "exec", "-T", "db", "pg_dump", "-U", user, "-d", database],
        check=True,
        capture_output=True,
    )
    path.write_bytes(result.stdout)
    logging.info("Резервная копия создана: %s", path)
    print(path)
except (OSError, subprocess.CalledProcessError):
    if path.exists():
        path.unlink()
    logging.exception("Ошибка создания резервной копии")
    raise
