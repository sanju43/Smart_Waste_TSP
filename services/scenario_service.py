from database.models import Project, Location

def create_default_project(session):
    p = Project(name="Exhibition Demo", description="Offline waste collection TSP scenario")
    session.add(p); session.flush(); return p

def active_locations(session, project_id):
    return session.query(Location).filter_by(project_id=project_id, is_active=True).order_by(Location.id).all()
