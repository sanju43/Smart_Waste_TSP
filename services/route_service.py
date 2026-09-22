from database.models import DistanceMatrix, Route, RoutePoint

def save_distance_matrix(session, project_id, locations, matrix):
    session.query(DistanceMatrix).filter_by(project_id=project_id).delete()
    for source in locations:
        for target in locations:
            session.add(DistanceMatrix(
                project_id=project_id,
                from_location_id=source.id,
                to_location_id=target.id,
                distance=float(matrix[source.id][target.id]),
            ))

def load_distance_matrix(session, project_id):
    rows = session.query(DistanceMatrix).filter_by(project_id=project_id).all()
    return {row.from_location_id: {} for row in rows} if not rows else {
        source: {r.to_location_id: r.distance for r in rows if r.from_location_id == source}
        for source in {r.from_location_id for r in rows}
    }

def save_route(session, project_id, route, algorithm, matrix, average_speed=30.0):
    old = session.query(Route).filter_by(project_id=project_id, status="completed").all()
    for item in old:
        item.status = "superseded"

    total = sum(matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))
    route_row = Route(
        project_id=project_id,
        algorithm=algorithm,
        start_location_id=route[0],
        total_distance=total,
        estimated_minutes=total / average_speed * 60,
        total_stops=max(0, len(route) - 2),
        status="completed",
    )
    session.add(route_row)
    session.flush()

    cumulative = 0.0
    for seq, location_id in enumerate(route, start=1):
        leg = 0.0 if seq == 1 else matrix[route[seq - 2]][location_id]
        cumulative += leg
        session.add(RoutePoint(
            route_id=route_row.id,
            location_id=location_id,
            sequence_no=seq,
            distance_from_previous=leg,
            cumulative_distance=cumulative,
        ))
    session.commit()
    return route_row

def latest_route(session, project_id):
    return (
        session.query(Route)
        .filter_by(project_id=project_id, status="completed")
        .order_by(Route.created_at.desc())
        .first()
    )

def invalidate_routes(session, project_id):
    session.query(Route).filter_by(project_id=project_id, status="completed").update(
        {"status": "invalidated"}, synchronize_session=False
    )
    session.commit()
