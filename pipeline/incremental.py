import logging

import pandas as pd
import psycopg2

from load_to_postgres import (
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
)

logger = logging.getLogger(__name__)


def filter_existing_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Incremental Load

    Read all existing business keys from PostgreSQL once,
    then filter new records in memory.

    Business Key:
        Company Name + Job Title + Location
    """

    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
    )

    cur = conn.cursor()

    # 一次性读取数据库所有业务键
    cur.execute("""
        SELECT
            c.name,
            j.title,
            j.location
        FROM jobs j
        JOIN companies c
            ON c.id = j.company_id;
        """)

    existing_keys = {
        (
            str(row[0]).strip().lower(),
            str(row[1]).strip().lower(),
            str(row[2]).strip().lower(),
        )
        for row in cur.fetchall()
    }

    cur.close()
    conn.close()

    logger.info(
        "Loaded %d existing business keys from PostgreSQL",
        len(existing_keys),
    )

    # Python 内存中过滤
    new_df = df[
        ~df.apply(
            lambda row: (
                str(row["Company Name"]).strip().lower(),
                str(row["Job Title"]).strip().lower(),
                str(row["Location"]).strip().lower(),
            )
            in existing_keys,
            axis=1,
        )
    ].copy()

    logger.info(
        "Incremental filter: input=%d new=%d skipped=%d",
        len(df),
        len(new_df),
        len(df) - len(new_df),
    )

    return new_df
