"""
diagnose.py — Run this to check everything before starting the Flask app.
Usage: python diagnose.py
"""

import sys
import os
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

print("=" * 60)
print("  Interview Trainer Agent — Diagnostic Check")
print("=" * 60)

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

all_ok = True

# ── 1. Python version ─────────────────────────────────────────────
v = sys.version_info
marker = PASS if v >= (3, 11) else WARN
print(f"\n{marker} Python {v.major}.{v.minor}.{v.micro}  (need 3.11+)")

# ── 2. Dependencies ───────────────────────────────────────────────
print("\n[CHECK] Required packages:")
packages = [
    ("flask",              "Flask"),
    ("dotenv",             "python-dotenv"),
    ("ibm_watsonx_ai",     "ibm-watsonx-ai"),
    ("langchain_ibm",      "langchain-ibm"),
    ("langchain_chroma",   "langchain-chroma"),
    ("chromadb",           "chromadb"),
    ("pdfplumber",         "pdfplumber"),
    ("gunicorn",           "gunicorn"),
]
for mod, pkg in packages:
    try:
        __import__(mod)
        print(f"  {PASS} {pkg}")
    except ImportError:
        print(f"  {FAIL} {pkg}  <-- run: pip install {pkg}")
        all_ok = False

# ── 3. .env credentials ───────────────────────────────────────────
print("\n[CHECK] Environment variables (.env):")
from dotenv import load_dotenv
load_dotenv()

creds = {
    "IBM_API_Key":             os.getenv("IBM_API_Key", ""),
    "IBM_Watsonx_Project_ID":  os.getenv("IBM_Watsonx_Project_ID", ""),
    "Watsonx_URL":             os.getenv("Watsonx_URL", ""),
}
for key, val in creds.items():
    if val.strip():
        # Show only the first 6 chars for security
        preview = val[:6] + "..." if len(val) > 6 else val
        print(f"  {PASS} {key} = {preview}")
    else:
        print(f"  {FAIL} {key} = MISSING  <-- add to .env")
        all_ok = False

# ── 4. Knowledge base files ───────────────────────────────────────
print("\n[CHECK] Knowledge base files:")
kb_dir = pathlib.Path("data/sample_kb")
if not kb_dir.exists():
    print(f"  {FAIL} data/sample_kb/ folder not found")
    all_ok = False
else:
    txt_files = sorted(kb_dir.glob("*.txt"))
    if not txt_files:
        print(f"  {FAIL} No .txt files in data/sample_kb/")
        all_ok = False
    else:
        for f in txt_files:
            print(f"  {PASS} {f.name}  ({f.stat().st_size // 1024} KB)")

# ── 5. ChromaDB vector store ──────────────────────────────────────
print("\n[CHECK] ChromaDB vector store (db/):")
db_dir = pathlib.Path("db")
if not db_dir.exists():
    print(f"  {FAIL} db/ not found — run: python src/ingest.py")
    all_ok = False
else:
    db_files = list(db_dir.rglob("*"))
    print(f"  {PASS} db/ exists  ({len(db_files)} files)")

# ── 6. Flask app ──────────────────────────────────────────────────
print("\n[CHECK] Flask application:")
try:
    from app import create_app
    app = create_app()
    rules = [str(r) for r in app.url_map.iter_rules()]
    print(f"  {PASS} Flask app created OK")
    print(f"  {PASS} Routes: {[r for r in rules if not r.startswith('/static')]}")
except Exception as e:
    print(f"  {FAIL} Flask app failed to load: {e}")
    all_ok = False

# ── 7. Templates & static files ───────────────────────────────────
print("\n[CHECK] Frontend files:")
for path, desc in [
    ("templates/base.html",   "base.html"),
    ("templates/index.html",  "index.html"),
    ("static/css/style.css",  "style.css"),
    ("static/js/app.js",      "app.js"),
]:
    p = pathlib.Path(path)
    if p.exists():
        print(f"  {PASS} {desc}  ({p.stat().st_size // 1024} KB)")
    else:
        print(f"  {FAIL} {desc} missing — check templates/ and static/")
        all_ok = False

# ── 8. Summary ────────────────────────────────────────────────────
print("\n" + "=" * 60)
if all_ok:
    print("  ALL CHECKS PASSED — ready to run!")
    print("\n  Start the app with:")
    print("    python app.py")
    print("  Then open: http://localhost:5000")
else:
    print("  SOME CHECKS FAILED — fix the items marked [FAIL] above.")
    print("\n  Quick fix checklist:")
    if not creds["IBM_API_Key"].strip():
        print("  1. Open .env and add:  IBM_API_Key = your_api_key")
    if not creds["IBM_Watsonx_Project_ID"].strip():
        print("  2. Open .env and add:  IBM_Watsonx_Project_ID = your_project_id")
    if not db_dir.exists():
        print("  3. Run: python src/ingest.py")
print("=" * 60)
