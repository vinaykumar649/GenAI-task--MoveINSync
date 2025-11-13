import os
import sys
import shutil
import glob

db_path = os.path.join(os.path.dirname(__file__), '..', 'moveinsync.db')

if os.path.exists(db_path):
    try:
        os.remove(db_path)
        print(f"Deleted old database: {db_path}")
    except Exception as e:
        print(f"Error deleting database: {e}")

cache_dirs = glob.glob(os.path.join(os.path.dirname(__file__), '**', '__pycache__'), recursive=True)
for cache_dir in cache_dirs:
    try:
        shutil.rmtree(cache_dir)
        print(f"Removed cache: {cache_dir}")
    except:
        pass

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

print("\nStarting application...")
exec(open('app.py').read())
