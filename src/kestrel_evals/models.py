from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PromptSpec(BaseModel):
    system: Optional[str] = None
    user: str


class EvalCheck(BaseModel):
    type: Literal["json_schema", "required_keys", "regex", "allowed_values"]
    # for json_schema
    json_schema: Optional[Dict[str, Any]] = None
    # for required_keys
    keys: Optional[List[str]] = None
    # for regex
    pattern: Optional[str] = None
    # for allowed_values
    path: Optional[str] = None  # e.g. "services"
    allowed: Optional[List[str]] = None


class EvalCase(BaseModel):
    id: str
    input: Dict[str, Any] = Field(default_factory=dict)
    prompt: PromptSpec
    checks: List[EvalCheck] = Field(default_factory=list)


class EvalSuite(BaseModel):
    name: str
    description: Optional[str] = None
    cases: List[EvalCase]
