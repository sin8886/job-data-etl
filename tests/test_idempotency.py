import os

import psycopg2
from dotenv import load_dotenv

from load_to_postgres import main

# 加载 .env
load_dotenv()


DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

CSV_PATH = r"D:\桌面\DE\data\clean\jobs_clean.csv"


def get_jobs_count():
    """
    查询 jobs 表数据量
    """
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM jobs;")

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count


def get_companies_count():
    """
    查询 companies 表数据量
    """
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM companies;")

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count


def test_idempotent_load():
    """
    测试 ETL 重复运行不会产生重复数据
    """

    # 第一次运行 ETL
    result1 = main(
        csv_path=CSV_PATH,
        db_name=DB_NAME,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
    )

    assert result1 == 0

    jobs_first = get_jobs_count()
    companies_first = get_companies_count()

    # 第二次运行 ETL
    result2 = main(
        csv_path=CSV_PATH,
        db_name=DB_NAME,
        db_user=DB_USER,
        db_password=DB_PASSWORD,
        db_host=DB_HOST,
        db_port=DB_PORT,
    )

    assert result2 == 0

    jobs_second = get_jobs_count()
    companies_second = get_companies_count()

    # 核心幂等验证
    assert jobs_first == jobs_second
    assert companies_first == companies_second
