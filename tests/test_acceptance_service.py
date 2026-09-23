from database.models import Base
from services.acceptance_service import run_full_acceptance
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def test_full_offline_exhibition_acceptance_flow():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, future=True)()

    checks = run_full_acceptance(session)

    assert checks
    assert all(check.status == "PASS" for check in checks), [
        (check.key, check.message) for check in checks if check.status != "PASS"
    ]
    assert {check.key for check in checks} >= {
        "demo_flow",
        "distance_matrix",
        "heuristic",
        "exact",
        "persistence",
        "animation",
        "presentation",
        "export",
        "results",
    }

    session.close()
