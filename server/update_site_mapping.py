import os
import csv
import sqlite3


def get_paths():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(repo_root, "mnt_data.db")
    mapping_txt = os.path.join(repo_root, "site mapping.txt")
    return db_path, mapping_txt


def parse_mapping(txt_path):
    mappings = []
    with open(txt_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # Normalize column names
            to_site = row.get('To Site') or row.get('To Site'.strip()) or row.get('To Site')
            subsidiary = row.get('Subsidiary') or None
            region = row.get('Region')
            country = row.get('Country') or None

            # Treat empty strings as NULL except when region == 'NA' (must stay 'NA')
            if subsidiary is not None:
                subsidiary = subsidiary.strip() or None
            if region is not None:
                region = region.strip()
                if region == '':
                    region = None
            if country is not None:
                country = country.strip() or None

            if to_site:
                mappings.append((to_site.strip(), subsidiary, region, country))
    return mappings


def recreate_table(db_path, mappings):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('DROP TABLE IF EXISTS site_mapping')
        cur.execute(
            '''CREATE TABLE site_mapping (
                to_site TEXT PRIMARY KEY,
                subsidiary TEXT,
                region TEXT,
                country TEXT
            )'''
        )

        cur.executemany(
            'INSERT INTO site_mapping (to_site, subsidiary, region, country) VALUES (?, ?, ?, ?)',
            mappings
        )
        conn.commit()
    finally:
        conn.close()


def verify(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM site_mapping')
        total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM site_mapping WHERE region='NA'")
        na_count = cur.fetchone()[0]

        print(f"Total rows inserted: {total}")
        print(f"Rows with region='NA': {na_count}")

        # show a few sample rows where region='NA'
        cur.execute("SELECT to_site, subsidiary, region, country FROM site_mapping WHERE region='NA' LIMIT 10")
        rows = cur.fetchall()
        if rows:
            print('\nSample rows with region=NA:')
            for r in rows:
                print(r)
    finally:
        conn.close()


def main():
    db_path, txt_path = get_paths()
    if not os.path.exists(txt_path):
        print(f"Mapping file not found: {txt_path}")
        return

    mappings = parse_mapping(txt_path)
    recreate_table(db_path, mappings)
    verify(db_path)


if __name__ == '__main__':
    main()
