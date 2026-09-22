def validate_locations(locations):
    depots = [x for x in locations if x.type == "Depot" and x.is_active]
    points = [x for x in locations if x.type != "Depot" and x.is_active]
    if len(depots) != 1: raise ValueError("Exactly one active depot is required.")
    if not points: raise ValueError("At least one active collection point is required.")
    return depots[0], points
