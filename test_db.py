from database import SessionLocal, Property

db = SessionLocal()
props = db.query(Property).all()
for p in props:
    print(f"Address: {p.address}")
    print(f"Est Value: {p.estimated_value}")
    print(f"Image: {p.image_url}")
    print("---")
db.close()
