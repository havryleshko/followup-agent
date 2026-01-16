from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List
from jsonschema import Draft202012Validator
from pydantic import BaseModel


def load_invoice_schema() -> dict:
    with Path("data/schemas/invoice_schema.json").open("r", encoding="utf-8") as f:
        return json.load(f)

class ValidationErrorInfo(BaseModel):
    row_index: int
    field_path: str
    message: str
    value: Any


class InvoiceValidationError(Exception):
    def __init__(self, errors: List[ValidationErrorInfo]) -> None:
        self.errors = errors
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        lines = ["Invoice validation failed:"]
        for error in self.errors:
            lines.append(
                f"Row {error.row_index} -> {error.field_path}: {error.message} "
                f"(got {error.value!r})"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class ValidationResult:
    valid_rows: List[dict]
    errors: List[ValidationErrorInfo]


def _format_field_path(path_parts: Iterable[Any]) -> str:
    path = ".".join(str(part) for part in path_parts)
    return path if path else "(root)"


def validate_row(row: dict, row_index: int, schema: dict) -> List[ValidationErrorInfo]:
    validator = Draft202012Validator(schema)
    errors: List[ValidationErrorInfo] = []
    for error in validator.iter_errors(row):
        errors.append(
            ValidationErrorInfo(
                row_index=row_index,
                field_path=_format_field_path(error.path),
                message=error.message,
                value=error.instance,
            )
        )
    return errors


def validate_rows(rows: List[dict]) -> ValidationResult:
    schema = load_invoice_schema()
    valid_rows: List[dict] = []
    errors: List[ValidationErrorInfo] = []
    for index, row in enumerate(rows, start=1):
        row_errors = validate_row(row, index, schema)
        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append(row)
    return ValidationResult(valid_rows=valid_rows, errors=errors)
