import os
import pathlib
import tempfile

# Point the app at a throwaway SQLite file and disable the scheduler before
# anything imports app.database / app.config.
_DB = pathlib.Path(tempfile.gettempdir()) / "nepcal_test.db"
_DB.unlink(missing_ok=True)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_DB}"
os.environ["SCHEDULER_ENABLED"] = "false"
