from services.presentation_service import get_presentation_steps


def test_presentation_has_complete_guided_flow():
    steps = get_presentation_steps()

    assert len(steps) == 6
    assert [step["title"] for step in steps] == [
        "The problem",
        "The input",
        "Measure distance",
        "Optimize the route",
        "Compare the result",
        "See the vehicle move",
    ]
    assert all(step["body"] for step in steps)


def test_presentation_explains_heuristic_limitation():
    steps = get_presentation_steps()
    optimization_step = next(step for step in steps if step["title"] == "Optimize the route")

    assert "Nearest Neighbor" in optimization_step["body"]
    assert "2-opt" in optimization_step["body"]
    assert "not guaranteed" in optimization_step["body"]
