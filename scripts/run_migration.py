#!/usr/bin/env python3
"""
scripts/run_migration.py
Run a SQL migration file against a Postgres database.
Usage:
  python scripts/run_migration.py --db-url <DATABASE_URL> --file migrations/001_create_model_tables.sql
  python scripts/run_migration.py --db-url <DATABASE_URL> --file migrations/001_create_model_tables_rollback.sql --rollback

Notes:
- Tries to use psycopg (modern), otherwise falls back to calling `psql` command.
"""
import argparse
import os
import subprocess
import sys


def run_with_psql(db_url, file_path):
    cmd = ['psql', db_url, '-f', file_path]
    print('Running:', ' '.join(cmd))
    res = subprocess.run(cmd)
    return res.returncode == 0


def run_with_psycopg(db_url, file_path):
    try:
        import psycopg
    except Exception:
        print('psycopg not installed; fallback to psql')
        return run_with_psql(db_url, file_path)

    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    try:
        conn = psycopg.connect(db_url)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        conn.close()
        return True
    except Exception as e:
        print('Error executing SQL via psycopg:', e)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', required=True, help='Postgres DATABASE_URL (postgres://)')
    parser.add_argument('--file', required=True, help='SQL file to execute')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print('File not found:', args.file)
        sys.exit(2)

    # prefer psycopg if available
    ok = run_with_psycopg(args.db_url, args.file)
    if not ok:
        print('Migration failed')
        sys.exit(1)
    print('Migration executed successfully')

if __name__ == '__main__':
    main()
