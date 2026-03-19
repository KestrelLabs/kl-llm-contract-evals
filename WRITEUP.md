# kestrel-evals — Deterministic LLM Gating (v1)

## What this is
`kestrel-evals` is a minimal evaluation harness for LLM-powered features where the output must obey a **contract**.

It runs YAML-defined eval suites, calls an LLM, then applies **deterministic checks** to decide pass/fail.

The key design choice is simple:

> **Deterministic gating first.**

No rubric scoring is required to get value. If your system depends on structured output (JSON fields, controlled vocabularies, required keys, basic formatting), deterministic checks can catch regressions early and consistently.

---

## Why deterministic gating first
Most LLM failures that break real systems are not subtle. They’re mechanical:
- missing keys
- wrong key names
- invalid JSON
- values outside a controlled vocabulary
- extra text / markdown wrappers

Those are ideal targets for deterministic checks.

This harness is meant to be used like a normal test runner:
- run locally while iterating
- run in CI
- fail the build if the contract breaks

---

## How it works (architecture)

### Inputs
- **Eval suite YAML** (example: `examples/structured_extraction.yaml`)
  - list of cases
  - each case defines:
    - prompt (system + user)
    - deterministic checks

### Execution
1) Load suite YAML
2) For each case:
   - call provider (v1: OpenAI) with system + user messages
   - collect raw `output_text`
3) Run checks against the output
4) Produce a JSON report
5) Exit non-zero if anything fails (CI gating)

Core code paths:
- Suite loading: `src/kestrel_evals/suite_loader.py`
- Runner: `src/kestrel_evals/runner.py`
- Checks: `src/kestrel_evals/checks.py`
- CLI: `src/kestrel_evals/cli.py`

---

## What checks are supported (v1)

`kestrel-evals` intentionally keeps dependencies light.

### 1) `json_schema` (minimal subset)
A small subset of JSON Schema is implemented to verify:
- output is a JSON object
- required keys exist
- basic types match (`string`, `array`, etc.)

Implementation: `check_json_schema()` in `src/kestrel_evals/checks.py`

### 2) `allowed_values`
Enforces a controlled vocabulary for a list field (ex: `services`).

This is critical for “routing/classification” style outputs where downstream code expects a known set of values.

### 3) `regex`
A simple regex check against raw `output_text`.

---

## Example suite: structured extraction

The included suite (`examples/structured_extraction.yaml`) models a common real problem:

> Extract a consistent JSON payload from messy inbound lead emails.

The contract enforced by this suite is:
- output is **only** JSON (no markdown, no code fences)
- output contains a fixed set of top-level keys
- unknown fields are empty strings (not `null`)
- `services` is an array of strings drawn from an allowlist

In other words, it’s a deliberately strict contract suitable for production pipelines.

---

## Running locally

```bash
cd KestrelLabs/kestrel-evals
python -m venv .venv
source .venv/bin/activate
pip install -e .

export OPENAI_API_KEY=...

kestrel-evals run examples/structured_extraction.yaml \
  --model gpt-4.1-mini \
  --out reports/report.json
```

### Outputs
- `reports/report.json` — the latest run (ignored by git)
- `baselines/structured_extraction-2026-03-19_gpt-4.1-mini.json` — known-good baseline snapshot

---

## CI gating

GitHub Actions workflow:
- `.github/workflows/evals.yml`

Key behavior:
- The CLI exits with **code 1** if `failed > 0`.
- The report JSON is uploaded as an artifact for inspection.

This means regressions show up as normal CI failures.

---

## Results (baseline)

A green baseline run is checked in here:

- `baselines/structured_extraction-2026-03-19_gpt-4.1-mini.json`

This baseline demonstrates:
- all cases passing under the enforced contract
- deterministic checks operating as a CI gate, not just a dashboard

---

## Design tradeoffs (intentional)

### Minimal deps
For v1, the harness avoids pulling in larger dependencies (ex: full `jsonschema`).

Benefit:
- small surface area
- easy to audit
- fast iteration

Cost:
- schema support is intentionally limited

### Strict output contracts
The example suite requires **raw JSON only**.

This is deliberate: if your downstream pipeline expects machine-parseable output, the evaluation should enforce the same constraints.

---

## Next improvements (v2 direction)
- Add provider abstraction + more providers (Anthropic, Azure OpenAI, local/OpenAI-compatible)
- Better report rendering (Markdown/HTML summaries)
- Dataset management (versioned inputs, baselines, diffs)
- Optional rubric scoring (LLM-as-judge) layered on top — but only after deterministic gating is solid
