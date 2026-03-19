# kestrel-evals

A minimal LLM evaluation harness designed for *Quick / Quiet / Quality* iteration.

## Goals (v1)
- Run YAML-defined eval suites locally and in CI
- Deterministic checks first (JSON schema / required keys / regex)
- Optional rubric scoring (LLM-as-judge) as an add-on
- OpenAI API support in Phase 1; keep the code structured to add providers in Phase 2

## Install (dev)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quickstart
```bash
export OPENAI_API_KEY=...

kestrel-evals run examples/structured_extraction.yaml \
  --model gpt-4.1-mini \
  --out reports/report.json
```

## Example suite format
See [`examples/structured_extraction.yaml`](./examples/structured_extraction.yaml).

This example also demonstrates an `allowed_values` check for enforcing a controlled vocabulary (e.g., the `services` array).

## Roadmap
- Provider abstraction + additional providers (Anthropic, Azure OpenAI, local/OpenAI-compatible)
- Better reporting (HTML/Markdown)
- Dataset management + baselines
