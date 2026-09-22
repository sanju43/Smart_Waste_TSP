from types import SimpleNamespace

import pytest

from services.route_simulation import animation_steps
from components.simulation import route_animation_figure


def location(i, name, x, y):
    return SimpleNamespace(id=i, name=name, x=x, y=y)


def test_animation_steps_follow_route_order():
    locations = [
        location(0, "Depot", 0, 0),
        location(1, "A", 2, 0),
        location(2, "B", 2, 2),
    ]
    steps = animation_steps(locations, [0, 1, 2, 0])

    assert len(steps) == 4
    assert [step["location_id"] for step in steps] == [0, 1, 2, 0]
    assert steps[1]["visited_ids"] == [0, 1]
    assert steps[-1]["visited_ids"] == [0, 1, 2, 0]
    assert (steps[-1]["vehicle_x"], steps[-1]["vehicle_y"]) == (0, 0)


def test_animation_rejects_unknown_location():
    locations = [location(0, "Depot", 0, 0)]
    with pytest.raises(ValueError, match="unknown location"):
        animation_steps(locations, [0, 9, 0])


def test_animation_figure_has_one_frame_per_route_step():
    locations = [
        location(0, "Depot", 0, 0),
        location(1, "A", 1, 0),
        location(2, "B", 1, 1),
    ]
    fig = route_animation_figure(locations, [0, 1, 2, 0])

    assert len(fig.frames) == 4
    assert len(fig.data) == 3
    assert fig.frames[-1].data[1].x == (0,)
    assert fig.frames[-1].data[1].y == (0,)
