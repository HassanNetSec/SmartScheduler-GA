import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check
from dataclasses import dataclass, field
from typing import Optional

# =====================================================
# VALID VALUES
# =====================================================

VALID_YEARS = {1, 2, 3, 4}

# =====================================================
# SCHEMA
# =====================================================

COURSE_SCHEMA = DataFrameSchema(
    columns={
        "course": Column(
            str,
            checks=[
                Check(lambda s: s.str.strip().str.len() > 0,
                      error="course cannot be empty"),
            ],
            nullable=False,
            coerce=True,
        ),
        "teacher": Column(
            str,
            checks=[
                Check(lambda s: s.str.strip().str.len() >= 3,
                      error="Teacher name must be at least 3 characters"),
                Check(lambda s: ~s.str.strip().str.match(r"^\d+$"),
                      error="Teacher name cannot be only numbers"),
            ],
            nullable=False,
            coerce=True,
        ),
        "group": Column(
            str,
            checks=[
                Check(lambda s: s.str.strip().str.len() > 0,
                      error="group cannot be empty"),
                Check(lambda s: s.str.strip().str.match(r"^[A-Za-z0-9\-]+$"),
                      error="group must be alphanumeric (e.g. BCS-6A, BAI-Batch)"),
            ],
            nullable=False,
            coerce=True,
        ),
        "credit_hours": Column(
            int,
            checks=[
                Check.isin({1, 2, 3, 4},
                           error="credit_hours must be 1, 2, 3, or 4"),
            ],
            nullable=True,
            coerce=True,
        ),
        "is_lab": Column(
            bool,
            nullable=True,
            coerce=True,
        ),
        "students": Column(
            int,
            checks=[
                Check(lambda s: s.ge(1), error="students must be at least 1"),
            ],
            nullable=True,
            coerce=True,
        ),
    },
    checks=[
        # Duplicate course+group combo
        Check(
            lambda df: ~df.duplicated(subset=["course", "group"], keep=False).any(),
            error="Duplicate (course + group) combinations found — each course/group pair must be unique",
        ),
        # Same teacher can't teach more courses than available weekly slots
        Check(
            lambda df: df.groupby("teacher")["course"].count().le(19).all(),
            error="A single teacher is assigned more than 19 courses — exceeds available weekly slots",
        ),
    ],
    coerce=True,
)

# =====================================================
# RESULT DATACLASS
# =====================================================

@dataclass
class ValidationResult:
    is_valid:   bool
    errors:     list[str]              = field(default_factory=list)
    warnings:   list[str]              = field(default_factory=list)
    cleaned_df: Optional[pd.DataFrame] = None

# =====================================================
# VALIDATOR
# =====================================================

def validate_courses_df(df: pd.DataFrame) -> ValidationResult:
    """
    Full validation pipeline:
      1. Required columns check
      2. Empty dataframe check
      3. Row-level cleaning (strip whitespace, normalise types)
      4. Pandera schema validation
      5. Soft warnings (non-blocking)

    Returns a ValidationResult with is_valid, errors, warnings, cleaned_df.
    """
    errors:   list[str] = []
    warnings: list[str] = []

    # ── 1. Required columns ───────────────────────────────────────────────────
    required = {"course", "teacher", "group"}
    missing  = required - set(df.columns)
    if missing:
        return ValidationResult(
            is_valid=False,
            errors=[
                f"Missing required column(s): {', '.join(sorted(missing))}. "
                f"Expected: course, teacher, group, credit_hours, is_lab, students"
            ],
        )

    # ── 2. Empty check ────────────────────────────────────────────────────────
    if df.empty:
        return ValidationResult(is_valid=False, errors=["The uploaded CSV has no data rows."])

    # ── 3. Clean ──────────────────────────────────────────────────────────────
    cleaned = df.copy()
    cleaned["course"]  = cleaned["course"].astype(str).str.strip()
    cleaned["teacher"] = cleaned["teacher"].astype(str).str.strip()
    cleaned["group"]   = cleaned["group"].astype(str).str.strip().str.upper()

    # Optional columns — add defaults if missing
    if "credit_hours" not in cleaned.columns:
        cleaned["credit_hours"] = 3
    if "is_lab" not in cleaned.columns:
        cleaned["is_lab"] = False
    else:
        # Normalise various truthy representations
        cleaned["is_lab"] = cleaned["is_lab"].map(
            lambda v: str(v).strip().lower() in {"true", "1", "yes"}
        )
    if "students" not in cleaned.columns:
        cleaned["students"] = 30

    # Drop completely empty rows silently
    before = len(cleaned)
    cleaned.dropna(subset=["course", "teacher", "group"], inplace=True)
    dropped = before - len(cleaned)
    if dropped > 0:
        warnings.append(f"{dropped} row(s) with empty course / teacher / group were removed.")

    if cleaned.empty:
        return ValidationResult(is_valid=False, errors=["All rows were empty after cleaning."])

    # ── 4. Pandera schema ─────────────────────────────────────────────────────
    try:
        validated = COURSE_SCHEMA.validate(cleaned, lazy=True)
    except pa.errors.SchemaErrors as exc:
        err_df = exc.failure_cases
        for _, row in err_df.iterrows():
            col      = row.get("column", "")
            case     = row.get("failure_case", "")
            check    = row.get("check", "")
            idx      = row.get("index", "")
            location = f"row {int(idx) + 2}" if pd.notna(idx) else "dataframe-level"
            if col:
                errors.append(f"[{location}] Column '{col}': {check} — got value: '{case}'")
            else:
                errors.append(f"[dataframe check] {check}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # ── 5. Soft warnings ──────────────────────────────────────────────────────
    lab_count = validated["is_lab"].sum()
    if lab_count == 0:
        warnings.append("No lab courses detected — all courses will be scheduled as lectures.")

    teachers_with_many = (
        validated.groupby("teacher")["course"]
        .count()
        .loc[lambda x: x >= 5]
    )
    for teacher, count in teachers_with_many.items():
        warnings.append(
            f"Teacher '{teacher}' is assigned {count} courses — verify this is intentional."
        )

    groups = validated["group"].nunique()
    if groups > 10:
        warnings.append(
            f"{groups} unique groups detected — GA generation may take longer for large inputs."
        )

    # Warn about groups with >18 courses (mathematically unschedulable in one week)
    group_counts = validated.groupby("group")["course"].count()
    overloaded   = group_counts[group_counts > 18]
    for grp, cnt in overloaded.items():
        warnings.append(
            f"Group '{grp}' has {cnt} courses — a max of 18 fit in a 5-day week. "
            f"{cnt - 18} course(s) will be unplaced unless the group is split."
        )

    return ValidationResult(
        is_valid=True,
        errors=errors,
        warnings=warnings,
        cleaned_df=validated,
    )