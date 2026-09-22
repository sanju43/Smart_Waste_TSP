from database.database import get_session, init_db
from database.models import Project, Location

DATA = [
    ("D0", "Depot", 10, 10, "Depot", 0, 1),
    ("P1", "School", 20, 15, "Collection", 50, 2),
    ("P2", "Market", 35, 12, "Collection", 80, 3),
    ("P3", "Society A", 45, 30, "Collection", 60, 2),
    ("P4", "Hospital", 30, 40, "Collection", 40, 3),
    ("P5", "Park", 15, 35, "Collection", 30, 1),
    ("P6", "Society B", 50, 45, "Collection", 70, 2),
]

def seed():
    init_db()
    s = get_session()
    try:
        if s.query(Project).first(): return
        p = Project(name="Default Exhibition Demo", description="Synthetic offline TSP dataset")
        s.add(p); s.flush()
        for code, name, x, y, typ, waste, priority in DATA:
            s.add(Location(project_id=p.id, name=f"{code} - {name}", type=typ, x=x, y=y, waste_kg=waste, priority=priority))
        s.commit()
    finally:
        s.close()

if __name__ == "__main__": seed()
