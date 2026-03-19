# kestrel-evals

A minimal LLM evaluation harness focused on **deterministic gating first**.

It runs YAML-defined eval suites (locally and in CI), executes the prompt(s), and then applies **deterministic checks** (schema/required keys/regex/allowed values) to decide pass/fail.

If any case fails, the CLI exits non-zero — so you can use it to **gate CI**.

- Full writeup: [`WRITEUP.md`](./WRITEUP.md)

## Goals (v1)
- Run YAML-defined eval suites locally and in CI
- Deterministic checks first (JSON schema / required keys / regex / allowed values)
- Optional rubric scoring (LLM-as-judge) as an add-on (later)
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

### Outputs
- `reports/report.json` — latest run (ignored by git)
- `baselines/structured_extraction-2026-03-19_gpt-4.1-mini.json` — known-good baseline snapshot (10/10 pass)

## Example suite format
See [`examples/structured_extraction.yaml`](./examples/structured_extraction.yaml).

This example demonstrates:
- enforcing an output contract via `json_schema`
- validating controlled vocabulary arrays via `allowed_values`
- simple content validation via `regex`

## CI
A minimal GitHub Actions workflow is included:
- [`.github/workflows/evals.yml`](./.github/workflows/evals.yml)

Because the CLI exits with `code=1` when any case fails, the workflow naturally fails on regressions.

## Roadmap
- Provider abstraction + additional providers (Anthropic, Azure OpenAI, local/OpenAI-compatible)
- Better reporting (HTML/Markdown)
- Dataset management + baselines
