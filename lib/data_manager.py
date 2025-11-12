# lib/data_manager.py
import pandas as pd
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parents[1] / "data"

# CSV filenames
USERS_CSV = DATA_DIR / "users.csv"
TASKS_CSV = DATA_DIR / "tasks.csv"
FILES_CSV = DATA_DIR / "files.csv"
AUDIT_CSV = DATA_DIR / "audit.csv"
COMM_CSV = DATA_DIR / "comm.csv"

def _read_csv(path):
    try:
        # parse_dates=False (we parse explicitly later where needed)
        return pd.read_csv(path)
    except FileNotFoundError:
        return pd.DataFrame()

def get_dataframes():
    """
    Return users, tasks, files, audit, comm in that order.
    Ensures the tasks DataFrame has required columns so pages can rely on their presence.
    """
    users = _read_csv(USERS_CSV)
    tasks = _read_csv(TASKS_CSV)
    files = _read_csv(FILES_CSV)
    audit = _read_csv(AUDIT_CSV)
    comm = _read_csv(COMM_CSV)

    # Normalize tasks columns (add missing columns with sensible defaults)
    expected = [
        "task_id", "title", "description", "assigned_to", "assigned_by",
        "due_date", "status", "priority", "team", "created_date", "completion_date"
    ]
    for col in expected:
        if col not in tasks.columns:
            tasks[col] = pd.NA

    # Convert common date columns to datetime if present and not already
    for date_col in ("due_date", "created_date", "completion_date"):
        if date_col in tasks.columns:
            try:
                tasks[date_col] = pd.to_datetime(tasks[date_col], errors="coerce")
            except Exception:
                tasks[date_col] = pd.NaT

    return users, tasks, files, audit, comm

def get_next_id(df, id_col):
    """Return next integer id for the specified column (1 if missing)."""
    if df is None or df.empty or id_col not in df.columns:
        return 1
    try:
        vals = pd.to_numeric(df[id_col], errors="coerce").dropna().astype(int)
        return int(vals.max()) + 1 if not vals.empty else 1
    except Exception:
        return 1

def quick_save(users=None, tasks=None, files=None, audit=None, comm=None):
    """
    Save provided DataFrames back to CSV. Only writes the DataFrames passed (None = skip).
    Returns True on success, False on failure.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if users is not None:
            users.to_csv(USERS_CSV, index=False)
        if tasks is not None:
            tasks.to_csv(TASKS_CSV, index=False)
        if files is not None:
            files.to_csv(FILES_CSV, index=False)
        if audit is not None:
            audit.to_csv(AUDIT_CSV, index=False)
        if comm is not None:
            comm.to_csv(COMM_CSV, index=False)
        return True
    except Exception as exc:
        print("quick_save error:", exc)
        return False
