import logging
import time
from typing import Optional
from pathlib import Path

import typer

from quality import check_row_count, check_null_rate, check_unique
from clean import DEFAULT_INPUT, DEFAULT_OUTPUT, run_pipeline
from load_to_postgres import (
    CSV_PATH,
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
    main as load_main,
)

app = typer.Typer()

DEFAULT_REPORT = "report.md"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def generate_report(df, report_path: str) -> None:
    total_rows = len(df)
    company_col = "Company Name"
    location_col = "Location"

    distinct_companies = None
    if company_col in df.columns:
        distinct_companies = int(df[company_col].nunique())

    top_locations = []
    if location_col in df.columns:
        counts = df[location_col].value_counts().head(10)
        top_locations = [(idx, int(val)) for idx, val in counts.items()]

    generated_at = time.strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Pipeline Report",
        "",
        f"- generated_at: {generated_at}",
        f"- rows: {total_rows}",
    ]

    if distinct_companies is not None:
        lines.append(f"- distinct_companies: {distinct_companies}")

    lines.extend(["", "## Top Locations", ""])
    if top_locations:
        for name, count in top_locations:
            lines.append(f"- {name}: {count}")
    else:
        lines.append("- (no location data)")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def compute_top_by_column(df, group_col: str, target_col: str, top_n: int = 1):
    """返回每个 group_col 下按 target_col 计数的 Top N（默认 Top 1）。

    返回 DataFrame，列名为 [group_col, target_col, count, rn]
    """
    # 1. 统计次数
    counts = df.groupby([group_col, target_col]).size().reset_index(name="count")

    # 2. 在每个 company 内按 count 排序并排名（使用 first 保证稳定）
    counts["rn"] = (
        counts.groupby(group_col)["count"]
        .rank(method="first", ascending=False)
        .astype(int)
    )

    # 3. 取 Top N
    result = (
        counts[counts["rn"] <= int(top_n)]
        .sort_values([group_col, "rn"])
        .reset_index(drop=True)
    )
    return result


def write_company_top_report(
    top_df, report_path: str, group_col: str, target_col: str, count_col: str = "count"
):
    """将 top_df 写成带有小节的 Markdown 报告。

    top_df 预期包含列: group_col, target_col, count_col，和可选的 rn
    会按 group_col 分组，每个公司写一段：公司名、Top 项目、Occurrences
    """
    lines = ["# Company Top Report", ""]

    # 按公司分组输出（保持出现顺序的稳定性）
    for company, group in top_df.groupby(group_col, sort=False):
        # 取第一行作为展示（若 top_n>1 可扩展）
        row = group.iloc[0]
        lines.append(str(company))
        lines.append("")
        lines.append(f"Top {target_col}:")
        lines.append(str(row[target_col]))
        lines.append("")
        lines.append("Occurrences:")
        lines.append(str(row.get(count_col, "")))
        lines.append("\n----------------\n")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_company_top_reports(df, output_base: str = "company_top_report") -> dict:
    """生成默认的 Top 岗位和 Top 技能报告并保存为 CSV + Markdown。

    返回生成的文件路径字典。
    """
    results = {}

    # Top job title
    top_jobs = compute_top_by_column(df, "Company Name", "Job Title", top_n=1)
    jobs_csv = f"{output_base}_jobs.csv"
    top_jobs.to_csv(jobs_csv, index=False)
    jobs_md = f"{output_base}_jobs.md"
    write_company_top_report(top_jobs, jobs_md, "Company Name", "Job Title")
    results["jobs_csv"] = jobs_csv
    results["jobs_md"] = jobs_md

    # Top skills: 如果存在 'Skill' 列则直接使用，否则尝试从 'Job Description' 中抽取（这里只做占位）
    if "Skill" in df.columns:
        top_skills = compute_top_by_column(df, "Company Name", "Skill", top_n=1)
        skills_csv = f"{output_base}_skills.csv"
        top_skills.to_csv(skills_csv, index=False)
        skills_md = f"{output_base}_skills.md"
        write_company_top_report(top_skills, skills_md, "Company Name", "Skill")
        results["skills_csv"] = skills_csv
        results["skills_md"] = skills_md
    else:
        # 如果没有 Skill 列，跳过并返回 info
        results["skills"] = "no Skill column found; skip"

    return results


def run_quality_checks(df):
    """
    Execute data quality checks.
    """

    results = []

    # 1. 行数检查
    results.append(check_row_count(df))

    # 2. 空值率检查
    results.append(check_null_rate(df, threshold=0.2))

    # 3. 唯一性检查
    # 检查ETL生成的唯一ID
    if "job_id" in df.columns:
        results.append(check_unique(df, "job_id"))

    return results


@app.command()
def run(
    mode: str = typer.Option("prod", help="Run mode label."),
    input_path: str = typer.Option(DEFAULT_INPUT, help="Input CSV path."),
    output_path: str = typer.Option(DEFAULT_OUTPUT, help="Clean CSV output path."),
    report_path: str = typer.Option(
        DEFAULT_REPORT, help="Markdown report output path."
    ),
    csv_path: Optional[str] = typer.Option(
        None, help="Override CSV path for load (defaults to clean output)."
    ),
    db_name: str = typer.Option(DB_NAME, help="Database name."),
    db_user: str = typer.Option(DB_USER, help="Database user."),
    db_password: Optional[str] = typer.Option(DB_PASSWORD, help="Database password."),
    db_host: str = typer.Option(DB_HOST, help="Database host."),
    db_port: str = typer.Option(DB_PORT, help="Database port."),
    skip_load: bool = typer.Option(False, help="Skip loading to database."),
    skip_report: bool = typer.Option(False, help="Skip report generation."),
    include_top_reports: bool = typer.Option(
        False,
        "--include-top-reports/--no-include-top-reports",
        help="Generate per-company top jobs/skills and save to artifacts (default: no)",
    ),
    append_to_report: bool = typer.Option(
        False,
        "--append-to-report/--no-append-to-report",
        help="If true and top reports generated, append them into main report.md",
    ),
):
    logger.info("pipeline start: mode=%s", mode)

    df = run_pipeline(input_path, output_path)

    # =========================
    # Data Quality Check
    # =========================

    quality_results = run_quality_checks(df)

    for result in quality_results:

        if result["passed"]:

            logger.info("Quality check passed: %s", result)

        else:

            logger.error("Quality check failed: %s", result)

            raise typer.Exit(code=1)

    if not skip_load:
        effective_csv = csv_path or output_path or CSV_PATH
        exit_code = load_main(
            effective_csv,
            db_name,
            db_user,
            db_password,
            db_host,
            db_port,
        )

        if exit_code != 0:
            raise typer.Exit(code=exit_code)

    if not skip_report:
        generate_report(df, report_path)
        logger.info("report written: path=%s", report_path)

        # 可选：生成每公司 Top 报告并写入 artifacts
        if include_top_reports:
            try:
                ts = time.strftime("%Y%m%d_%H%M%S")
                artifacts_dir = Path("artifacts") / ts
                artifacts_dir.mkdir(parents=True, exist_ok=True)

                output_base = str(artifacts_dir / "company_top")
                company_results = generate_company_top_reports(
                    df, output_base=output_base
                )

                if append_to_report:

                    def _append_if_exists(src_path, dest_path):
                        if isinstance(src_path, str) and Path(src_path).exists():
                            with open(src_path, "r", encoding="utf-8") as sf, open(
                                dest_path, "a", encoding="utf-8"
                            ) as dfp:
                                dfp.write("\n\n")
                                dfp.write(sf.read())

                    jobs_md = company_results.get("jobs_md")
                    _append_if_exists(jobs_md, report_path)

                    skills_md = company_results.get("skills_md")
                    if skills_md:
                        _append_if_exists(skills_md, report_path)

                logger.info("generated company top reports in: %s", artifacts_dir)

            except Exception:
                logger.exception("failed to generate/append company top reports")

    logger.info("pipeline done")


if __name__ == "__main__":
    app()
