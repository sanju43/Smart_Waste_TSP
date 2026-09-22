from database.models import Project, Location

def create_default_project(session):
    p = Project(name="Exhibition Demo", description="Offline waste collection TSP scenario")
    session.add(p)
    session.flush()
    return p

def active_locations(session, project_id):
    return session.query(Location).filter_by(project_id=project_id, is_active=True).order_by(Location.id).all()

def get_projects(session):
    return session.query(Project).order_by(Project.id).all()

def get_project(session, project_id):
    return session.get(Project, project_id)

def delete_project(session, project_id):
    p = session.get(Project, project_id)
    if not p:
        return False
    session.delete(p)
    session.commit()
    return True
