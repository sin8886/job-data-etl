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
    """加载YAML配置，支持环境变量覆盖"""
    config_file = config_path or os.getenv("ETL_CLEAN_CONFIG_FILE") or CONFIG_FILE
    config_file = Path(config_file)
    
    if not config_file.exists():
        logger.warning(f"配置文件不存在: {config_file}，使用默认值")
        return {}
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    
    logger.info(f"已加载配置: {config_file}")
    return config


CLEAN_CONFIG = load_config()
DEFAULT_INPUT = CLEAN_CONFIG.get("input_path", r"D:\桌面\DE\data\raw\DataAnalyst.csv")
DEFAULT_OUTPUT = CLEAN_CONFIG.get("output_path", r"D:\桌面\DE\data\clean\jobs_clean.csv")


def load_data(file_path, config=None):
    """加载原始数据。"""
    return pd.read_csv(file_path)


def _ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def drop_configured_columns(df, config=None):
    """删除配置文件里指定的列。"""
    cfg = config or CLEAN_CONFIG
    drop_cols = _ensure_list(cfg.get("drop_columns", ["Unnamed: 0"]))
    if not drop_cols:
        return df
    return df.drop(columns=drop_cols, errors="ignore")


def replace_invalid_values(df, config=None):
    """把无效值统一替换成空值。"""
    cfg = config or CLEAN_CONFIG
    invalid_values = cfg.get("replace_invalid_values", {-1: None})
    result = df.copy()
    for old_val, new_val in invalid_values.items():
        result = result.replace(old_val, new_val)
    return result


def clean_company_names(df, config=None):
    """清洗公司名字段。"""
    cfg = config or CLEAN_CONFIG
    company_config = cfg.get("company_name", {})
    if not company_config.get("enabled", True):
        return df

    result = df.copy()
    split_on = company_config.get("split_on", "\n")
    split_index = company_config.get("split_index", 0)
    for col in _ensure_list(company_config.get("columns", ["Company Name"])):
        if col in result.columns:
            result[col] = result[col].str.split(split_on).str[split_index]
    return result


def clean_salary_estimates(df, config=None):
    """清洗薪资估算字段。"""
    cfg = config or CLEAN_CONFIG
    salary_config = cfg.get("salary_estimate", {})
    if not salary_config.get("enabled", True):
        return df

    result = df.copy()
    replace_texts = _ensure_list(salary_config.get("replace_texts", ["(Glassdoor est.)"]))
    for col in _ensure_list(salary_config.get("columns", ["Salary Estimate"])):
        if col in result.columns:
            for text in replace_texts:
                result[col] = result[col].str.replace(text, "", regex=False)
    return result


def clean_company_and_salary(df, config=None):
    """兼容旧调用：按顺序执行公司名和薪资清洗。"""
    result = replace_invalid_values(df, config)
    result = clean_company_names(result, config)
    result = clean_salary_estimates(result, config)
    return result


def remove_duplicates(df, config=None):
    """去重。"""
    cfg = config or CLEAN_CONFIG
    dedup_config = cfg.get("dedup", {})
    if dedup_config.get("enabled", True):
        return df.drop_duplicates()
    return df


def save_data(df, output_path):
    """保存清洗后的结果。"""
    df.to_csv(output_path, index=False)


def _log_missing_rates(df, columns, warn_threshold=0.30):
    total = len(df)
    if total == 0:
        logger.warning("清洗后数据为空：rows=0")
        return

    summary_parts = []
    warning_parts = []

    for col in columns:
        if col not in df.columns:
            logger.warning("缺少列（无法统计缺失率）：%s", col)
            continue

        missing = int(df[col].isna().sum())
        rate = missing / total
        summary_parts.append(f"{col}={missing}/{total}({rate:.1%})")
        if rate >= warn_threshold:
            warning_parts.append(f"{col}({rate:.1%})")

    if summary_parts:
        logger.info("关键列缺失率: %s", "; ".join(summary_parts))
    if warning_parts:
        logger.warning("高缺失列(>=%.0f%%): %s", warn_threshold * 100, ", ".join(warning_parts))


def run_pipeline(input_path, output_path, config=None):
    """主执行逻辑：把每一步小函数串起来。"""
    cfg = config or CLEAN_CONFIG
    start = time.perf_counter()
    logger.info("开始清洗: input=%s", input_path)

    try:
        # 1. 加载
        df = load_data(input_path, cfg)
        df = drop_configured_columns(df, cfg)
        raw_rows = len(df)
        logger.info("读取成功: rows=%d cols=%d", raw_rows, len(df.columns))

        # 2. 清洗
        df = replace_invalid_values(df, cfg)
        df = clean_company_names(df, cfg)
        df = clean_salary_estimates(df, cfg)
        before_dedup = len(df)
        df = remove_duplicates(df, cfg)
        after_dedup = len(df)
        logger.info(
            "去重完成: before=%d after=%d removed=%d",
            before_dedup,
            after_dedup,
            before_dedup - after_dedup,
        )

        # 3. 缺失率（关键列）
        missing_config = cfg.get("missing_rate", {})
        _log_missing_rates(
            df,
            columns=missing_config.get("columns", ["Company Name", "Salary Estimate", "Location", "Job Title", "Industry"]),
            warn_threshold=missing_config.get("warn_threshold", 0.30),
        )

        # 4. 保存
        save_data(df, output_path)
        logger.info("写入完成: output=%s", output_path)

        elapsed = time.perf_counter() - start
        logger.info("清洗完成: final_rows=%d elapsed=%.2fs", len(df), elapsed)
        return df

    except Exception:
        logger.exception("清洗流程失败")
        raise


@app.command()
def run(
    input_path: str = typer.Option(DEFAULT_INPUT, help="Input CSV path."),
    output_path: str = typer.Option(DEFAULT_OUTPUT, help="Output CSV path."),
):
    run_pipeline(input_path, output_path)


if __name__ == "__main__":
    app()