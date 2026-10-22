import stat

from dotenv import dotenv_values
import pytest

import setup_env


@pytest.mark.parametrize("model, expected", [("", "llama3.2:3b"), ("custom-model", "custom-model")])
def test_write_local_model(monkeypatch, tmp_path, capsys, model, expected):
    monkeypatch.setattr(setup_env, "BASE_DIR", tmp_path)
    prompts = []
    def answer(prompt):
        prompts.append(prompt)
        return model
    monkeypatch.setattr("builtins.input", answer)
    setup_env.main()
    path = tmp_path / ".env"
    assert dotenv_values(path, interpolate=False) == {"APP_OLLAMA_MODEL": expected}
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert len(prompts) == 1
    assert "key" not in prompts[0].lower()
    assert "No API key is needed" in capsys.readouterr().out


@pytest.mark.parametrize("model", ["bad\nINJECTED=value", "example:cloud"])
def test_reject_invalid_model(monkeypatch, tmp_path, model):
    monkeypatch.setattr(setup_env, "BASE_DIR", tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: model)
    setup_env.main()
    assert not (tmp_path / ".env").exists()
