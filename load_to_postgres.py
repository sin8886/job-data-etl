import logging
import os
import time

import pandas as pd
import psycopg2
import typer


LOG_FILE = os.getenv("ETL_LOG_FILE", "etl.log")
FILE_LOG_LEVEL = os.getenv("ETL_FILE_LEVEL", "INFO").upper()
CONSOLE_LOG_LEVEL = os.getenv("ETL_CONSOLE_LEVEL", "INFO").upper()

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(getattr(logging, FILE_LOG_LEVEL, logging.INFO))

_console_handler = logging.StreamHandler()
_console_handler.setLevel(getattr(logging, CONSOLE_LOG_LEVEL, logging.INFO))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[_file_handler, _console_handler],
)

logger = logging.getLogger(__name__)
app = typer.Typer()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_env_file(file_name: str) -> bool:
    file_path = file_name if os.path.isabs(file_name) else os.path.join(BASE_DIR, file_name)
    if not os.path.exists(file_path):
        return False

    loaded = 0
    with open(file_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)
                loaded += 1

    logger.info("已加载环境变量文件: %s keys=%d", file_path, loaded)
    return True


def _load_env_config() -> None:
    explicit_file = os.getenv("ETL_ENV_FILE")
    if explicit_file:
        if not _load_env_file(explicit_file):
            logger.warning("指定的环境变量文件不存在: %s", explicit_file)
        return

    if _load_env_file(".env"):
        return
    _load_env_file("env")


_load_env_config()


CSV_PATH = r"D:\\桌面\\DE\\data\\clean\\jobs_clean.csv"

DB_NAME = os.getenv("PGDATABASE") or os.getenv("DB_NAME") or "job_db"
DB_USER = os.getenv("PGUSER") or os.getenv("DB_USER") or "postgres"
DB_PASSWORD = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("PGHOST") or os.getenv("DB_HOST") or "localhost"
DB_PORT = os.getenv("PGPORT") or os.getenv("DB_PORT") or "5432"


def main(
    csv_path: str,
    db_name: str,
    db_user: str,
    db_password: str | None,
    db_host: str,
    db_port: str,
) -> int:
    start = time.perf_counter()
    logger.info("日志输出: file=%s file_level=%s console_level=%s", LOG_FILE, FILE_LOG_LEVEL, CONSOLE_LOG_LEVEL)

    if not db_password:
        logger.error("未提供数据库密码：请在 .env/env 或系统环境变量中设置 PGPASSWORD 或 DB_PASSWORD")
        return 4

    # 1. 读取 clean 数据
    try:
        df = pd.read_csv(csv_path)
        df = df.where(pd.notna(df), None)
        logger.info("CSV 读取成功: path=%s rows=%d cols=%d", csv_path, len(df), len(df.columns))
    except Exception as e:
        logger.error("CSV 读取失败: path=%s err=%s", csv_path, e)
        return 1

    # 2. 连接 PostgreSQL
    conn = None
    cur = None
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )
        cur = conn.cursor()
        logger.info("数据库连接成功: db=%s host=%s port=%s user=%s", db_name, db_host, db_port, db_user)

        # 提醒：重复运行会插入重复 jobs（目前未做幂等/upsert）
        try:
            cur.execute("SELECT COUNT(*) FROM jobs;")
            existing_jobs = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM companies;")
            existing_companies = int(cur.fetchone()[0])
            if existing_jobs > 0 or existing_companies > 0:
                logger.warning(
                    "检测到表已有数据：jobs=%d companies=%d。重复运行会追加数据（可能产生重复）。",
                    existing_jobs,
                    existing_companies,
                )
        except Exception:
            # 不阻塞主流程
            logger.debug("无法读取现有行数（忽略）", exc_info=True)
        logger.info("开始同步数据到 PostgreSQL...")

        companies_inserted = 0
        companies_existing = 0
        jobs_inserted = 0
        rows_skipped = 0

        for idx, row in df.iterrows():
            company_name = None
            job_title = None
            try:
                # ========= Step A：处理公司 =========

                company_name = row["Company Name"]
                job_title = row["Job Title"]

                # 公司名为空，直接跳过
                if company_name is None or str(company_name).strip() == "":
                    rows_skipped += 1
                    continue

                company_name = str(company_name).strip()

                # 先查公司是否存在
                cur.execute(
                    "SELECT id FROM companies WHERE name = %s LIMIT 1;",
                    (company_name,),
                )

                result = cur.fetchone()

                if result:
                    company_id = result[0]
                    companies_existing += 1
                else:
                    cur.execute(
                        """
                        INSERT INTO companies (name, industry, sector, rating, revenue, headquarters, size, founded)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (
                            company_name,
                            row["Industry"],
                            row["Sector"],
                            row["Rating"],
                            row["Revenue"],
                            row["Headquarters"],
                            row["Size"],
                            row["Founded"],
                        ),
                    )

                    company_id = cur.fetchone()[0]
                    companies_inserted += 1

                # ========= Step B：插入 jobs =========

                cur.execute(
                    """
                    INSERT INTO jobs (title, company_id, location, salary_estimate, easy_apply)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        row["Job Title"],
                        company_id,
                        row["Location"],
                        row["Salary Estimate"],
                        row["Easy Apply"],
                    ),
                )
                jobs_inserted += 1
            except Exception as e:
                conn.rollback()
                logger.error(
                    "入库失败（已回滚）: row_index=%s company=%r title=%r err=%s",
                    idx,
                    company_name,
                    job_title,
                    e,
                )
                return 2

        # 3. 提交事务
        conn.commit()
        elapsed = time.perf_counter() - start
        logger.info(
            "ETL 导入成功: companies_inserted=%d companies_existing=%d jobs_inserted=%d rows_skipped=%d elapsed=%.2fs",
            companies_inserted,
            companies_existing,
            jobs_inserted,
            rows_skipped,
            elapsed,
        )
        return 0

    except Exception as e:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        logger.error("数据库连接/初始化失败: err=%s", e)
        return 3
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()


@app.command()
def run(
    csv_path: str = typer.Option(CSV_PATH, help="Clean CSV path."),
    db_name: str = typer.Option(DB_NAME, help="Database name."),
    db_user: str = typer.Option(DB_USER, help="Database user."),
    db_password: str = typer.Option(DB_PASSWORD, help="Database password."),
    db_host: str = typer.Option(DB_HOST, help="Database host."),
    db_port: str = typer.Option(DB_PORT, help="Database port."),
):
    exit_code = main(csv_path, db_name, db_user, db_password, db_host, db_port)
    raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()