from algorithms.validators import validate_route
from database.models import DistanceMatrix, Route, RoutePoint


def save_distance_matrix(session, project_id, locations, matrix):
    session.query(DistanceMatrix).filter_by(project_id=project_id).delete()
    for source in locations:
        for target in locations:
            if source.id not in matrix or target.id not in matrix[source.id]:
                raise ValueError("Distance matrix is incomplete; route calculation was not saved.")
            session.add(DistanceMatrix(
                project_id=project_id,
                from_location_id=source.id,
                to_location_id=target.id,
                distance=float(matrix[source.id][target.id]),
            ))
    session.commit()


def load_distance_matrix(session, project_id):
    rows = session.query(DistanceMatrix).filter_by(project_id=project_id).all()
    matrix = {}
    for row in rows:
        matrix.setdefault(row.from_location_id, {})[row.to_location_id] = row.distance
    return matrix


def save_route(session, project_id, route, algorithm, matrix, average_speed=30.0):
    if average_speed <= 0:
        raise ValueError("Average vehicle speed must be greater than zero.")
    if len(route) < 3:
        raise ValueError("A route requires a depot and at least one collection point.")

    collection_ids = route[1:-1]
    validate_route(route, route[0], collection_ids)

    old = session.query(Route).filter_by(project_id=project_id, status="completed").all()
    for item in old:
        item.status = "superseded"

    try:
        total = sum(float(matrix[route[i]][route[i + 1]]) for i in range(len(route) - 1))
    except KeyError as exc:
        session.rollback()
        raise ValueError("Saved route cannot be calculated because the distance matrix is incomplete.") from exc

    route_row = Route(
        project_id=project_id,
        algorithm=algorithm,
        start_location_id=route[0],
        total_distance=total,
        estimated_minutes=total / average_speed * 60,
        total_stops=len(collection_ids),
        status="completed",
    )
    session.add(route_row)
    session.flush()

    cumulative = 0.0
    for seq, location_id in enumerate(route, start=1):
        leg = 0.0 if seq == 1 else float(matrix[route[seq - 2]][location_id])
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
