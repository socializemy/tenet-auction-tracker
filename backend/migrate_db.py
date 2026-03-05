import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "auction_data.db")

def migrate():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Check existing columns
    c.execute("PRAGMA table_info(properties)")
    columns = [row[1] for row in c.fetchall()]
    
    new_cols = []
    if "lot_size" not in columns:
        c.execute("ALTER TABLE properties ADD COLUMN lot_size VARCHAR")
        new_cols.append("lot_size")
    if "property_type" not in columns:
        c.execute("ALTER TABLE properties ADD COLUMN property_type VARCHAR")
        new_cols.append("property_type")
    if "year_built" not in columns:
        c.execute("ALTER TABLE properties ADD COLUMN year_built INTEGER")
        new_cols.append("year_built")
    if "apn" not in columns:
        c.execute("ALTER TABLE properties ADD COLUMN apn VARCHAR")
        new_cols.append("apn")
        
    conn.commit()
    conn.close()
    
    if new_cols:
        print(f"Migration completed. Added columns: {', '.join(new_cols)}")
    else:
        print("Database already up to date. No new columns added.")

if __name__ == "__main__":
    migrate()
