from __future__ import annotations

from pathlib import Path

import yaml

from .models import EvalSuite


def load_suite(path: str | Path) -> EvalSuite:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return EvalSuite.model_validate(data)
