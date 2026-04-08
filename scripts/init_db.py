from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db.init_db import create_all_tables


def main() -> None:
    create_all_tables()
    print("database tables created")


if __name__ == "__main__":
    main()
