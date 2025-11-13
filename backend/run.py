import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

db_path = os.path.join(os.path.dirname(__file__), '..', 'moveinsync.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print("[OK] Old database deleted - will recreate with fresh data")

# Clear bytecode cache
import shutil
import glob

cache_dirs = glob.glob('**/__pycache__', recursive=True)
for cache_dir in cache_dirs:
    try:
        shutil.rmtree(cache_dir)
        print(f"[OK] Removed cache: {cache_dir}")
    except:
        pass

exec(open('app.py').read())
