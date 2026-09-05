import logging
import os
import time
from pathlib import Path

import pandas as pd
import typer
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
app = typer.Typer()

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "clean_config.yaml"


def load_config(config_path=None):
    """Load YAML configuration with optional environment variable overrides."""
    config_file = config_path or os.getenv("ETL_CLEAN_CONFIG_FILE") or CONFIG_FILE
    config_file = Path(config_file)

    if not config_file.exists():
        logger.warning(f"Configuration file not found: {config_file}; using defaults")
        return {}

    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    logger.info(f"Configuration loaded: {config_file}")
    return config


CLEAN_CONFIG = load_config()
DEFAULT_INPUT = CLEAN_CONFIG.get("input_path", r"D:\桌面\DE\data\raw\DataAnalyst.csv")
DEFAULT_OUTPUT = CLEAN_CONFIG.get(
    "output_path", r"D:\桌面\DE\data\clean\jobs_clean.csv"
)


def load_data(file_path, config=None):
    """Load raw data from a CSV file."""
    return pd.read_csv(file_path)


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def drop_configured_columns(df, config=None):
    """Drop columns configured in the YAML file."""
    cfg = config or CLEAN_CONFIG
    drop_cols = _ensure_list(cfg.get("drop_columns", ["Unnamed: 0"]))
    if not drop_cols:
        return df
    return df.drop(columns=drop_cols, errors="ignore")


def replace_invalid_values(df, config=None):
    """Replace configured invalid values with null values."""
    cfg = config or CLEAN_CONFIG
    invalid_values = cfg.get("replace_invalid_values", {-1: None})
    result = df.copy()
    for old_val, new_val in invalid_values.items():
        result = result.replace(old_val, new_val)
    return result


def clean_company_names(df, config=None):
    """Clean configured company name fields."""
    cfg = config or CLEAN_CONFIG
    company_config = cfg.get("company_name", {})
    if not company_config.get("enabled", True):
        return df

    result = df.copy()
    split_on = company_config.get("split_on", "\n")
    split_index = company_config.get("split_index", 0)
    for col in _ensure_list(company_config.get("columns", ["Company Name"])):
        if col in result.columns:
            result[col] = result[col].str.split(split_on).str[split_index].str.strip()
    return result


def clean_salary_estimates(df, config=None):
    """Clean configured salary estimate fields."""
    cfg = config or CLEAN_CONFIG
    salary_config = cfg.get("salary_estimate", {})
    if not salary_config.get("enabled", True):
        return df

    result = df.copy()
    replace_texts = _ensure_list(
        salary_config.get("replace_texts", ["(Glassdoor est.)"])
    )
    for col in _ensure_list(salary_config.get("columns", ["Salary Estimate"])):
        if col in result.columns:
            for text in replace_texts:
                result[col] = result[col].str.replace(text, "", regex=False)
    return result


def clean_company_and_salary(df, config=None):
    """Preserve compatibility by cleaning company names and salaries in order."""
    result = replace_invalid_values(df, config)
    result = clean_company_names(result, config)
    result = clean_salary_estimates(result, config)
    return result


def remove_duplicates(df, config=None):
    """Remove duplicate records when enabled in the configuration."""
    cfg = config or CLEAN_CONFIG
    dedup_config = cfg.get("dedup", {})
    if dedup_config.get("enabled", True):
        return df.drop_duplicates()
    return df


def save_data(df, output_path):
    """Save the cleaned data to a CSV file."""
    df.to_csv(output_path, index=False)


def _log_missing_rates(df, columns, warn_threshold=0.30):
    total = len(df)
    if total == 0:
        logger.warning("Cleaned data is empty: rows=0")
        return

    summary_parts = []
    warning_parts = []

    for col in columns:
        if col not in df.columns:
            logger.warning("Missing column; cannot calculate null rate: %s", col)
            continue

        missing = int(df[col].isna().sum())
        rate = missing / total
        summary_parts.append(f"{col}={missing}/{total}({rate:.1%})")
        if rate >= warn_threshold:
            warning_parts.append(f"{col}({rate:.1%})")

    if summary_parts:
        logger.info("Critical-column null rates: %s", "; ".join(summary_parts))
    if warning_parts:
        logger.warning(
            "Columns with high null rates (>=%.0f%%): %s",
            warn_threshold * 100,
            ", ".join(warning_parts),
        )


def run_pipeline(input_path, output_path, config=None):
    """Run the main data-cleaning pipeline."""
    cfg = config or CLEAN_CONFIG
    start = time.perf_counter()
    logger.info("Cleaning started: input=%s", input_path)

    try:
        # 1. Load
        df = load_data(input_path, cfg)
        df = drop_configured_columns(df, cfg)
        raw_rows = len(df)
        logger.info("Read successfully: rows=%d cols=%d", raw_rows, len(df.columns))

        # 2. Clean
        df = replace_invalid_values(df, cfg)
        df = clean_company_names(df, cfg)
        df = clean_salary_estimates(df, cfg)
        before_dedup = len(df)
        df = remove_duplicates(df, cfg)
        after_dedup = len(df)
        logger.info(
            "Deduplication completed: before=%d after=%d removed=%d",
            before_dedup,
            after_dedup,
            before_dedup - after_dedup,
        )
        # Generate a unique job ID.
        df.insert(0, "job_id", range(1, len(df) + 1))
        # 3. Calculate null rates for critical columns.
        missing_config = cfg.get("missing_rate", {})
        _log_missing_rates(
            df,
            columns=missing_config.get(
                "columns",
                [
                    "Company Name",
                    "Salary Estimate",
                    "Location",
                    "Job Title",
                    "Industry",
                ],
            ),
            warn_threshold=missing_config.get("warn_threshold", 0.30),
        )

        # 4. Save
        save_data(df, output_path)
        logger.info("Write completed: output=%s", output_path)

        elapsed = time.perf_counter() - start
        logger.info("Cleaning completed: final_rows=%d elapsed=%.2fs", len(df), elapsed)
        return df

    except Exception:
        logger.exception("Cleaning pipeline failed")
        raise


@app.command()
def run(
    input_path: str = typer.Option(DEFAULT_INPUT, help="Input CSV path."),
    output_path: str = typer.Option(DEFAULT_OUTPUT, help="Output CSV path."),
):
    run_pipeline(input_path, output_path)


if __name__ == "__main__":
    app()
