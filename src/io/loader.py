from __future__ import annotations
import re
from pathlib import Path
from typing import Any, List
import pandas as pd
from src.state import InvoiceRow
from src.utils.validation import InvoiceValidationError, validate_rows


EXPECTED_COLUMNS = [
    "client_name",
    "invoice_id",
    "invoice_amount",
    "currency",
    "invoice_issue_date",
    "days_overdue",
    "last_followup_date",
    "relationship_tag",
    "notes",
]


def load_invoices(path: str) -> List[InvoiceRow]:
    df = _read_file(path)
    rows = _normalize_df(df)
    validation = validate_rows(rows)
    if validation.errors:
        raise InvoiceValidationError(validation.errors)
    return [InvoiceRow(**row) for row in validation.valid_rows]


def _read_file(path: str) -> pd.DataFrame:
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"File not found: {path_obj}")

    suffix = path_obj.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path_obj, dtype=str)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path_obj, dtype=str)
    raise ValueError(f"Unsupported file type: {suffix}")


def _normalize_df(df: pd.DataFrame) -> List[dict]:
    df = df.copy()
    df.columns = [
        str(col).strip().lower().replace(" ", "_") for col in df.columns
    ]

    for column in EXPECTED_COLUMNS:
        if column not in df.columns:
            df[column] = None

    _coerce_dates(df, ["invoice_issue_date", "last_followup_date"])
    _coerce_numeric(df, "invoice_amount")
    _coerce_integer(df, "days_overdue")

    rows: List[dict] = []
    for raw_row in df.to_dict(orient="records"):
        row = {key: _normalize_missing(value) for key, value in raw_row.items()}
        row["currency"] = _default_currency(row.get("currency"))
        row["notes"] = _default_notes(row.get("notes"))
        row["relationship_tag"] = _normalize_relationship_tag(
            row.get("relationship_tag")
        )
        row["client_name"] = _clean_string(row.get("client_name"))
        row["invoice_id"] = _clean_string(row.get("invoice_id"))
        rows.append(row)
    return rows


def _normalize_missing(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    if pd.isna(value):
        return None
    return value


def _clean_string(value: Any) -> Any:
    if value is None:
        return None
    return str(value).strip()


def _default_currency(value: Any) -> str:
    cleaned = _clean_string(value)
    return cleaned if cleaned else "USD"


def _default_notes(value: Any) -> str:
    cleaned = _clean_string(value)
    return cleaned if cleaned is not None else ""


def _normalize_relationship_tag(value: Any) -> Any:
    cleaned = _clean_string(value)
    if cleaned is None:
        return None
    return cleaned.lower()


def _coerce_dates(df: pd.DataFrame, cols: List[str]) -> None:
    for col in cols:
        parsed = pd.to_datetime(df[col], errors="coerce")
        df[col] = parsed.dt.strftime("%Y-%m-%d")


def _coerce_numeric(df: pd.DataFrame, col: str) -> None:
    df[col] = df[col].apply(_parse_float)


def _coerce_integer(df: pd.DataFrame, col: str) -> None:
    df[col] = df[col].apply(_parse_int)


def _parse_float(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[^\d.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_int(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[^\d.\-]", "", text)
    if text in {"", "-", ".", "-."}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None
