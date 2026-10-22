# pytest tests/test_doctor.py
# python -m pytest tests/test_doctor.py

import json
from evryn.core.doctor import run_doctor_checks, print_doctor_report


def test_doctor_structure():
    rep = run_doctor_checks()
    assert isinstance(rep, dict)
    assert "status" in rep
    assert rep["status"] in ("HEALTHY", "DEGRADED", "WARNING")
    assert "checks" in rep
    assert isinstance(rep["checks"], list)
    assert len(rep["checks"]) >= 15
    for c in rep["checks"]:
        assert "name" in c
        assert "category" in c
        assert "passed" in c
        assert "details" in c
        assert "remediation" in c


def test_doctor_execution_healthy():
    rep = run_doctor_checks()
    assert rep["passed_count"] >= 15
    code = print_doctor_report(rep, as_json=False)
    assert code == 0


def test_doctor_json_output(capsys):
    rep = run_doctor_checks()
    code = print_doctor_report(rep, as_json=True)
    assert code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["status"] == rep["status"]
    assert len(data["checks"]) == len(rep["checks"])
