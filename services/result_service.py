def route_metrics(route, distance, average_speed=30.0):
    total = sum(distance[route[i]][route[i+1]] for i in range(len(route)-1))
    return {"total_distance": total, "estimated_minutes": total / average_speed * 60, "stops": max(0, len(route)-2)}

def compare(baseline, improved, distance):
    b = route_metrics(baseline, distance)["total_distance"]
    o = route_metrics(improved, distance)["total_distance"]
    saved = b-o
    return {"baseline": b, "improved": o, "saved": saved, "percent_saved": (saved/b*100 if b else 0)}
