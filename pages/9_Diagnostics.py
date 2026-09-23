import streamlit as st

from database.database import get_session
from services.diagnostics_service import run_diagnostics, run_test_suite

st.set_page_config(page_title="Diagnostics", page_icon="🩺", layout="wide")
st.title("Diagnostics")
st.caption("Offline health checks for the exhibition application.")

session = get_session()
try:
    checks = run_diagnostics(session)

    passed = sum(check.status == "PASS" for check in checks)
    warnings = sum(check.status == "WARNING" for check in checks)
    failed = sum(check.status == "FAIL" for check in checks)

    c1, c2, c3 = st.columns(3)
    c1.metric("Passed", passed)
    c2.metric("Warnings", warnings)
    c3.metric("Failed", failed)

    if failed:
        st.error("One or more checks require attention.")
    elif warnings:
        st.warning("Core checks pass, but some non-blocking conditions were detected.")
    else:
        st.success("All application health checks passed.")

    for check in checks:
        icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}[check.status]
        with st.expander(f"{icon} {check.label} — {check.status}", expanded=check.status == "FAIL"):
            st.write(check.message)

    st.divider()
    st.subheader("Automated test suite")
    st.caption("Runs the existing pytest suite locally using the current Python environment.")

    if st.button("Run pytest diagnostics", type="primary"):
        with st.spinner("Running tests..."):
            result = run_test_suite()
        if result["ok"]:
            st.success("Pytest completed successfully.")
        elif result["timed_out"]:
            st.error("Pytest timed out after 60 seconds.")
        else:
            st.error(f"Pytest failed with exit code {result['returncode']}.")
        st.code(result["output"] or "No test output.", language="text")

    st.divider()
    st.subheader("Exhibition readiness")
    st.markdown(
        """
- Keep the machine offline during the core demonstration.
- Start with **Start Demo** and verify the depot and collection points appear.
- Run **Optimize Route** and confirm the route returns to the depot.
- Open **Results & Comparison** and verify distance/time metrics.
- Use **Presentation Mode** for the guided explanation.
- Use **Reports & Export** only when a saved result needs to be shared.
"""
    )
finally:
    session.close()
