# kestrel-evals

[![ci](https://github.com/KestrelLabs/kl-llm-contract-evals/actions/workflows/ci.yml/badge.svg)](https://github.com/KestrelLabs/kl-llm-contract-evals/actions/workflows/ci.yml)
[![evals](https://github.com/KestrelLabs/kl-llm-contract-evals/actions/workflows/evals.yml/badge.svg)](https://github.com/KestrelLabs/kl-llm-contract-evals/actions/workflows/evals.yml)
[![evals results](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/KestrelLabs/kl-llm-contract-evals/master/badges/evals.json&cacheSeconds=60)](https://github.com/KestrelLabs/kl-llm-contract-evals/actions/workflows/evals.yml)

A **small evaluation harness** for generating **empirical evidence** about whether an LLM reliably satisfies a *contract*.

The core idea is intentionally narrow: run YAML-defined eval suites, then apply **deterministic checks** (schema / required keys / regex / allowed values). If any case fails, the run is considered a failure.

This repo is meant to be more like a **public experiment / whitepaper companion** than a large general-purpose tool.

- Full writeup: [`WRITEUP.md`](./WRITEUP.md)

---

## What this repo is (and isn’t)

### It *is*
- A reproducible way to run contract-style eval suites and produce a JSON report
- A reference implementation for “deterministic gating first”
- A place to publish **baselines + results artifacts** that support the writeup

### It is *not*
- A full research eval framework
- A feature-complete dataset/benchmark platform
- A multi-provider orchestration system (yet)

---

## Key concepts (glossary)

- **Suite**: a YAML file describing a set of test cases.
- **Case**: one prompt + expected constraints (schema, regexes, allowed values, etc.).
- **Deterministic checks**: validation that does *not* require an LLM judge.
- **Provider**: the model backend. Phase 1 targets **OpenAI**.

---

## Install

> Requires Python >= 3.10 (CI runs 3.11/3.12).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# For basic CLI + suite loading (no API calls)
pip install -e .

# To actually run eval suites against OpenAI
pip install -e ".[openai]"
```

---

## Quickstart (run an eval suite)

```bash
export OPENAI_API_KEY=...

kestrel-evals run examples/structured_extraction.yaml \
  --model gpt-4.1-mini \
  --out reports/report.json
```

- The command exits **non-zero** if any cases fail.
- This makes it usable as a **CI gate**, even though the repo itself is primarily an experiment.

---

## Outputs

### `reports/report.json`
Primary machine-readable output.

At minimum it contains:
- `summary.total`
- `summary.failed`

…and per-case results (pass/fail + details).

### `baselines/…`
Known-good snapshots for particular suites/models.

Example:
- `baselines/structured_extraction-2026-03-19_gpt-4.1-mini.json` — baseline snapshot (10/10 pass)

> `reports/` outputs are typically local artifacts; baselines are meant to be committed when you want a durable reference point.

---

## CI workflows (and what the badges mean)

This repo includes two GitHub Actions workflows:

### 1) `ci.yml` (runs on push/PR)
Sanity checks only:
- installs the package
- compile/import checks
- loads an example suite

This does **not** call any LLM APIs.

### 2) `evals.yml` (manual)
Runs an eval suite against OpenAI:
- requires `OPENAI_API_KEY` configured as a GitHub Actions secret
- uploads `reports/report.json` as an artifact
- updates `badges/evals.json` so the “evals results” badge shows the **model + pass rate**

> Note: calling models costs money. Keep suites small and intentional.

---

## Example suite format

See: [`examples/structured_extraction.yaml`](./examples/structured_extraction.yaml)

This example demonstrates:
- enforcing an output contract via `json_schema`
- validating controlled vocabulary arrays via `allowed_values`
- simple content validation via `regex`

---

## Reproducing the writeup / generating empirical data

This repo is designed so a reader can:
1. Inspect the suite(s) in `examples/`
2. Run them against a specified model
3. View the machine-readable report output
4. Compare against the committed baseline(s)

The intent is not to publish a perfect benchmark; it’s to make the claims in the writeup falsifiable with a small, auditable harness.

---

## Roadmap (small)

- Provider abstraction + additional providers (Anthropic, Azure OpenAI, local/OpenAI-compatible)
- Better reporting (HTML/Markdown)
- Baseline comparison helpers (diff/regression summaries)

---

## License

See [`LICENSE`](./LICENSE).
