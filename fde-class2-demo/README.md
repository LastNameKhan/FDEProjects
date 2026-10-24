# Meridian Retail support draft review

A small CLI that uses a local Ollama model to draft replies for human review.
It cannot send messages, approve refunds, or change records. It uses the existing
`cases.json` and `policy.md` beside `app.py`.

## Setup

Install [Ollama](https://ollama.com/download), then download the default local model:

```sh
ollama pull llama3.2:3b
```

Start the Ollama desktop app, or run `ollama serve` in another terminal.
Model download requires internet access; subsequent generation uses the local
server. Use a locally downloaded model rather than an Ollama cloud model.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install python-dotenv==1.2.1 pytest==8.4.2
python setup_env.py
python app.py --case C1
```

Setup asks only for the model name (default `llama3.2:3b`) and writes or replaces
this project's `.env` with owner-only permissions. No API key is needed.
The app reads `APP_OLLAMA_MODEL` from the process environment or project `.env`;
process values take precedence. It ignores all previous OpenAI settings.
You can also skip setup and use the default model. To switch models, download
one with `ollama pull MODEL_NAME` and enter that name during setup.

The app posts to `http://localhost:11434/api/generate` using Python's standard
library, JSON mode, and non-streaming output, as described in the
[Ollama API documentation](https://docs.ollama.com/api/generate). There is no
OpenAI dependency or cloud fallback. Proxy settings are bypassed, HTTP redirects
are rejected, and model names containing `cloud` are rejected. Keep the local
Ollama server configured for local inference.

Requests have a 20-second socket timeout and no automatic retries. Cold model
loading or slow generation may time out; warm up with `ollama run llama3.2:3b`
and try again. Missing models, a stopped server, malformed/incomplete responses,
and validation errors produce an empty draft, `UNAVAILABLE`, and manual fallback
instructions without a traceback or stale draft.

## Run and test

```sh
python app.py --case C1
python app.py --case C2 --offline-demo
python app.py --case C3 --simulate-timeout
python -m pytest -q
```

Only C1, C2, and C3 are accepted. Offline and timeout modes are mutually exclusive
and make no model call. Offline results are labelled prerecorded synthetic
examples. Input paths are relative to `app.py`, independent of the current
working directory. Tests use fake models and fake HTTP responses; app tests
block network connections and do not require Ollama.

Output has three sections: SUPPLIED FACTS, SUPPLIED POLICY, and DRAFT RESULT FOR
HUMAN REVIEW. Model results must contain exactly `draft_reply` (text),
`evidence_refs` (list of known policy IDs), `missing_information` (list of field
names), and `review_status` (`READY_FOR_HUMAN_REVIEW`, `NEEDS_INFORMATION`, or
`BLOCKED`). `UNAVAILABLE` is a local failure state, never an accepted model status.
Correct structure and known policy references do not prove correct content.
A human must verify facts, policy applicability, and wording before acting.
The app calculates the current timestamp in Python and checks `delivery_date`.
Delivery between zero and 78 hours ago (inclusive) is eligible for human refund
review (`READY_FOR_HUMAN_REVIEW`). More than 78 hours produces a recommendation
to reject the refund under P1 (`BLOCKED`). Missing, invalid, or future dates need
clarification (`NEEDS_INFORMATION`). Date-only values mean midnight in the
machine's local timezone. Full ISO timestamps must include a timezone.

The timestamp and computed refund assessment are supplied to Ollama. After
validating the model response, the final draft uses the application's standard
policy wording so model errors cannot reverse eligibility or request an already
supplied valid date. The timestamp used is printed for human review. Provider
errors still produce `UNAVAILABLE`. No refund is automatically approved or
rejected in any external system; these are draft recommendations only.
Offline demos are fixed synthetic snapshots at `recorded_at`, not live date checks.

## Dependencies and verification

The three originally requested pins remain in `requirements.txt`;
`anthropic` is unused and the OpenAI SDK has been removed. The available package
index did not provide `anthropic==1.5.0` or `python-dotenv==1.2.3`, so the complete
original requirements cannot currently be installed from that index. The setup
command above uses the available versions used for verification in the existing
Python 3.9.6 virtual environment: `python-dotenv==1.2.1` and `pytest==8.4.2`.
The full original pinned set has not been tested.

Ollama and `llama3.2:3b` were subsequently installed and live cases were run.
Tests use mocked HTTP responses and cover the inclusive 78-hour boundary,
local-midnight date handling, timezone offsets, invalid dates, and contradictory
model output.
