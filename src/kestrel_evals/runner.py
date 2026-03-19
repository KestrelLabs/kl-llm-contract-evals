from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .checks import (
    check_allowed_values,
    check_json_schema,
    check_regex,
    check_required_keys,
    try_parse_json,
)
from .models import EvalCase, EvalSuite
from .providers.base import LLMProvider


@dataclass
class CaseResult:
    id: str
    passed: bool
    output_text: str
    parsed_json: Optional[Any]
    checks: List[Dict[str, Any]]


async def run_suite(*, suite: EvalSuite, provider: LLMProvider, model: str) -> Dict[str, Any]:
    results: List[CaseResult] = []

    for case in suite.cases:
        out = await provider.generate(model=model, system=case.prompt.system, user=case.prompt.user)

        checks_out: List[Dict[str, Any]] = []
        all_ok = True
        parsed_json = None

        for chk in case.checks:
            if chk.type in ("json_schema", "required_keys"):
                ok, obj, msg = try_parse_json(out)
                parsed_json = obj if ok else None
                if not ok:
                    checks_out.append({"type": chk.type, "ok": False, "detail": msg})
                    all_ok = False
                    continue

                if chk.type == "required_keys":
                    ok2, msg2 = check_required_keys(obj, chk.keys or [])
                    checks_out.append({"type": "required_keys", "ok": ok2, "detail": msg2})
                    all_ok = all_ok and ok2
                elif chk.type == "json_schema":
                    ok2, msg2 = check_json_schema(obj, chk.json_schema or {})
                    checks_out.append({"type": "json_schema", "ok": ok2, "detail": msg2})
                    all_ok = all_ok and ok2

            elif chk.type == "regex":
                ok2, msg2 = check_regex(out, chk.pattern or "")
                checks_out.append({"type": "regex", "ok": ok2, "detail": msg2})
                all_ok = all_ok and ok2

            elif chk.type == "allowed_values":
                ok, obj, msg = try_parse_json(out)
                if not ok:
                    checks_out.append({"type": "allowed_values", "ok": False, "detail": msg})
                    all_ok = False
                    continue
                ok2, msg2 = check_allowed_values(obj, path=chk.path or "", allowed=chk.allowed or [])
                checks_out.append({"type": "allowed_values", "ok": ok2, "detail": msg2})
                all_ok = all_ok and ok2

            else:
                checks_out.append({"type": chk.type, "ok": False, "detail": "Unknown check type"})
                all_ok = False

        results.append(
            CaseResult(
                id=case.id,
                passed=all_ok,
                output_text=out,
                parsed_json=parsed_json,
                checks=checks_out,
            )
        )

    passed = sum(1 for r in results if r.passed)
    report = {
        "suite": {"name": suite.name, "description": suite.description},
        "model": model,
        "summary": {"total": len(results), "passed": passed, "failed": len(results) - passed},
        "cases": [
            {
                "id": r.id,
                "passed": r.passed,
                "checks": r.checks,
                "output_text": r.output_text,
            }
            for r in results
        ],
    }
    return report
