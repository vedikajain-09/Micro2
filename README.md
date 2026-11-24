# Hostel Management System (Fixed - No SQLAlchemy)

This version uses only **Flask + Python's built-in sqlite3**.  
It no longer depends on Flask-SQLAlchemy, so it works on Windows, Python 3.11/3.12/3.13, and machines with Application Control policies.

## Setup

1. Extract the archive
2. Open terminal / PowerShell **inside** the `hostel_management` folder
3. Install:

```bash
python -m pip install -r requirements.txt
```

4. Run:

```bash
python app.py
```

5. Open http://localhost:5000

## Demo Credentials

**Warden:** `warden` / `admin123`  
**Student:** `student1` / `pass123` (up to student8)

The database (`hostel.db`) is created automatically next to `app.py` and seeded with sample data.