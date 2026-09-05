import logging

import pandas as pd
import psycopg2

from load_to_postgres import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)

logger = logging.getLogger(__name__)


def _normalize_key_part(value) -> str:
    """Apply the same case/whitespace rule used by the database company index."""
    return str(value).strip().lower()


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

    # Load all existing business keys in one query.
    cur.execute("""
        SELECT
            lower(btrim(c.name)),
            lower(btrim(j.title)),
            lower(btrim(j.location))
        FROM jobs j
        JOIN companies c
            ON c.id = j.company_id;
        """)

    existing_keys = {
        (
            _normalize_key_part(row[0]),
            _normalize_key_part(row[1]),
            _normalize_key_part(row[2]),
        )
        for row in cur.fetchall()
    }

    cur.close()
    conn.close()

    logger.info(
        "Loaded %d existing business keys from PostgreSQL",
        len(existing_keys),
    )

    # Filter records in memory.
    new_df = df[
        ~df.apply(
            lambda row: (
                _normalize_key_part(row["Company Name"]),
                _normalize_key_part(row["Job Title"]),
                _normalize_key_part(row["Location"]),
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
