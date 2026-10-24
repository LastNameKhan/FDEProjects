import json
import io
from datetime import datetime, timedelta, timezone

import pytest

import app


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    import socket
    def blocked(*args, **kwargs):
        raise AssertionError("External network access is forbidden in tests")
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


def demo(case="C1"):
    return json.loads((app.BASE_DIR / "demo_outputs.json").read_text())["results"][case]


def no_model(*args):
    pytest.fail("Model must not be called")


def test_success(capsys):
    def fake(case, policy):
        assert case["case_id"] == "C1"
        assert "P1." in policy
        return demo()
    now = datetime(2026, 10, 25, tzinfo=timezone.utc)
    facts = json.loads((app.BASE_DIR / "cases.json").read_text())["C1"]
    assert app.run("C1", model_fn=fake, now=now) == app.refund_assessment(facts, now)
    out = capsys.readouterr().out
    for heading in ("SUPPLIED FACTS", "SUPPLIED POLICY", "DRAFT RESULT FOR HUMAN REVIEW"):
        assert heading in out
    assert "does not prove content correctness" in out


@pytest.mark.parametrize("bad", [None, "not json", {},
    {**demo(), "extra": True}, {**demo(), "draft_reply": 3},
    {**demo(), "evidence_refs": "P1"}, {**demo(), "evidence_refs": [1]},
    {**demo(), "evidence_refs": ["P99"]}, {**demo(), "missing_information": None},
    {**demo(), "missing_information": [False]}, {**demo(), "review_status": []},
    {**demo(), "review_status": "UNAVAILABLE"}])
def test_invalid_output(bad, capsys):
    assert app.run("C1", model_fn=lambda *args: bad) == app.unavailable()
    assert app.FALLBACK in capsys.readouterr().out


@pytest.mark.parametrize("error", [TimeoutError, RuntimeError, json.JSONDecodeError])
def test_provider_failure(error, capsys):
    def fake(*args):
        if error is json.JSONDecodeError:
            raise error("secret", "bad", 0)
        raise error("secret")
    assert app.run("C1", model_fn=fake) == app.unavailable()
    assert "secret" not in capsys.readouterr().out


def test_simulated_timeout(capsys):
    assert app.run("C1", simulate_timeout=True, model_fn=no_model) == app.unavailable()
    out = capsys.readouterr().out
    assert "no model API was called" in out
    assert app.FALLBACK in out


@pytest.mark.parametrize("case", ["C1", "C2", "C3"])
def test_inputs_and_offline(case, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    result = app.run(case, offline_demo=True, model_fn=no_model)
    assert result == demo(case)
    assert "PRERECORDED SYNTHETIC RESULT — no model API was called" in capsys.readouterr().out
    facts = json.loads((app.BASE_DIR / "cases.json").read_text())
    assert facts[case]["case_id"] == case
    policy = (app.BASE_DIR / "policy.md").read_text()
    for policy_id in ("P1.", "P2.", "P3.", "P4."):
        assert policy_id in policy


@pytest.mark.parametrize("filename", ["cases.json", "policy.md", "demo_outputs.json"])
def test_bad_input(filename, tmp_path):
    for source in ("cases.json", "policy.md", "demo_outputs.json"):
        (tmp_path / source).write_text((app.BASE_DIR / source).read_text())
    (tmp_path / filename).write_text("" if filename == "policy.md" else "invalid JSON")
    assert app.run("C1", offline_demo=True, base_dir=tmp_path, model_fn=no_model) == app.unavailable()


def test_no_stale_draft():
    assert app.run("C1", model_fn=lambda *args: demo())["draft_reply"]
    assert app.run("C1", simulate_timeout=True, model_fn=no_model)["draft_reply"] == ""


def test_ollama_configuration(monkeypatch, tmp_path):
    demo_result = demo()
    monkeypatch.setattr(app, "BASE_DIR", tmp_path)
    (tmp_path / ".env").write_text("APP_OLLAMA_MODEL='local-model'\n")
    monkeypatch.delenv("APP_OLLAMA_MODEL", raising=False)
    calls = []
    class FakeOpener:
        def open(self, request, timeout):
            calls.append((request, timeout))
            return io.BytesIO(json.dumps({"done": True, "response": json.dumps(demo_result)}).encode())
    monkeypatch.setattr(app.urllib.request, "build_opener", lambda *args: FakeOpener())
    assert app.model_result({"case_id": "C1"}, "P1. policy") == demo_result
    request, timeout = calls[0]
    assert request.full_url == "http://localhost:11434/api/generate"
    assert timeout == 20.0
    payload = json.loads(request.data)
    assert payload["model"] == "local-model"
    assert payload["format"] == "json"
    assert payload["stream"] is False
    assert "Authorization" not in request.headers
    monkeypatch.setenv("APP_OLLAMA_MODEL", "process-model")
    app.model_result({}, "P1. policy")
    assert json.loads(calls[1][0].data)["model"] == "process-model"
    monkeypatch.setenv("APP_OLLAMA_MODEL", "")
    app.model_result({}, "P1. policy")
    assert json.loads(calls[2][0].data)["model"] == app.DEFAULT_MODEL


@pytest.mark.parametrize("response", [
    {"done": False, "response": "{}"},
    {"done": True, "error": "failed", "response": "{}"},
    {"done": True, "done_reason": "length", "response": "{}"},
    {"done": True, "response": "invalid JSON"},
    {"done": True},
])
def test_bad_ollama_response(monkeypatch, response):
    class FakeOpener:
        def open(self, *args, **kwargs):
            return io.BytesIO(json.dumps(response).encode())
    monkeypatch.setattr(app.urllib.request, "build_opener", lambda *args: FakeOpener())
    assert app.run("C1") == app.unavailable()


def test_cloud_model_rejected(monkeypatch):
    monkeypatch.setenv("APP_OLLAMA_MODEL", "example:cloud")
    monkeypatch.setattr(app.urllib.request, "build_opener", no_model)
    assert app.run("C1") == app.unavailable()


def test_project_files():
    for name in ("app.py", "README.md", "requirements.txt", "setup_env.py", ".env.example",
                 ".gitignore", "demo_outputs.json", "test_app.py", "test_setup_env.py"):
        assert (app.BASE_DIR / name).is_file()
    pins = (app.BASE_DIR / "requirements.txt").read_text().splitlines()
    assert {"anthropic==1.5.0", "python-dotenv==1.2.3", "pytest==9.1.1"} <= set(pins)



def test_model_cannot_reverse_eligibility():
    supplied = json.loads((app.BASE_DIR / "cases.json").read_text())["C1"]
    contradictory = {"draft_reply": "Please provide delivery_date.", "evidence_refs": ["P2"],
                     "missing_information": ["delivery_date"], "review_status": "NEEDS_INFORMATION"}
    now = datetime(2026, 10, 25, tzinfo=timezone.utc)
    def fake(case, policy):
        assert case["delivery_date"] == supplied["delivery_date"]
        assert case["checked_at"] == now.isoformat()
        assert case["refund_assessment"]["review_status"] == "BLOCKED"
        return contradictory
    result = app.run("C1", model_fn=fake, now=now)
    assert result == app.refund_assessment(supplied, now)
    assert result["missing_information"] == []
    assert "reject" in result["draft_reply"]


@pytest.mark.parametrize("hours, status", [(0, "READY_FOR_HUMAN_REVIEW"),
    (77.999, "READY_FOR_HUMAN_REVIEW"), (78, "READY_FOR_HUMAN_REVIEW"),
    (78.001, "BLOCKED"), (100, "BLOCKED"), (-1, "NEEDS_INFORMATION")])
def test_78_hour_boundary(hours, status):
    delivered = datetime(2026, 10, 20, 12, tzinfo=timezone.utc)
    result = app.refund_assessment({"delivery_date": delivered.isoformat(), "issue_status": "open"},
                                   delivered + timedelta(hours=hours))
    assert result["review_status"] == status
    assert "issue remains open" in result["draft_reply"]
    if status != "NEEDS_INFORMATION":
        assert result["missing_information"] == []
    if status == "READY_FOR_HUMAN_REVIEW":
        assert "not a refund approval" in result["draft_reply"]


@pytest.mark.parametrize("value", [None, "", "bad", "2026-02-30", 5, "2026-10-20T12:00:00"])
def test_bad_delivery_date(value):
    result = app.refund_assessment({"delivery_date": value}, datetime(2026, 10, 25, tzinfo=timezone.utc))
    assert result["review_status"] == "NEEDS_INFORMATION"
    assert result["missing_information"] == ["delivery_date"]


def test_date_only_uses_local_midnight():
    delivered = datetime(2026, 10, 20).astimezone()
    result = app.refund_assessment({"delivery_date": "2026-10-20"}, delivered + timedelta(hours=78))
    assert result["review_status"] == "READY_FOR_HUMAN_REVIEW"


def test_timestamp_timezone_equivalence():
    now = datetime(2026, 10, 23, 18, tzinfo=timezone.utc)
    a = app.refund_assessment({"delivery_date": "2026-10-20T12:00:00Z"}, now)
    b = app.refund_assessment({"delivery_date": "2026-10-20T17:30:00+05:30"}, now)
    assert a["review_status"] == b["review_status"] == "READY_FOR_HUMAN_REVIEW"
