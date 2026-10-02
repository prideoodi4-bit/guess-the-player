"""Consistent SQLite backup, including when a WAL writer is running."""
import argparse
import os
import sqlite3
from pathlib import Path
from bot import ROOT,load_env

def backup(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if not source.is_file():
        raise SystemExit('Database does not exist yet; start a game first.')
    if source==output:
        raise SystemExit('Backup must use a different destination.')
    if output.exists():
        raise SystemExit('Destination already exists; use a new backup filename.')
    output.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src, sqlite3.connect(output) as dst:
        src.backup(dst)
    return output

if __name__=='__main__':
    load_env()
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    parser.add_argument('--source',default=os.getenv('DB_PATH',str(ROOT/'state'/'game.sqlite3')))
    args=parser.parse_args()
    print(backup(args.source,args.output))
