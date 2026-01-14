#!/usr/bin/env python3
"""
scripts/verify_migration.py
Simple checks to verify expected tables/columns exist after migration.
Usage:
  python scripts/verify_migration.py --db-url <DATABASE_URL>
"""
import argparse
import psycopg

EXPECTED_TABLES = {
    'estandar_versions': ['id','estandar_id','parametros','version_number'],
    'model_snapshots': ['id','evento_id','inputs','outputs','parameters'],
    'model_deltas': ['id','evento_id','ton_model','kg_model'],
    'audit_logs': ['id','entidad']
}


def check_tables(db_url):
    conn = psycopg.connect(db_url)
    cur = conn.cursor()
    issues = []
    for table, cols in EXPECTED_TABLES.items():
        cur.execute("SELECT to_regclass(%s)", (table,))
        exists = cur.fetchone()[0]
        if not exists:
            issues.append(f"Missing table: {table}")
            continue
        # check columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        existing_cols = [r[0] for r in cur.fetchall()]
        for c in cols:
            if c not in existing_cols:
                issues.append(f"Table {table} missing column {c}")
    cur.close(); conn.close()
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db-url', required=True)
    args = parser.parse_args()

    issues = check_tables(args.db_url)
    if issues:
        print('Verification issues found:')
        for i in issues:
            print(' -', i)
        raise SystemExit(2)
    print('All expected tables and columns present.')

if __name__ == '__main__':
    main()
