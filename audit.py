from datetime import datetime, timezone

import psycopg2

from load_to_postgres import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


def get_db_config():

    return {
        "dbname": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "host": DB_HOST,
        "port": DB_PORT,
    }


def create_run(run_type="incremental"):

    conn = psycopg2.connect(**get_db_config())

    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO pipeline_runs
        (
            started_at,
            status,
            run_type
        )
        VALUES
        (
            %s,
            %s,
            %s
        )
        RETURNING run_id;
        """,
        (
            datetime.now(timezone.utc),
            "RUNNING",
            run_type,
        ),
    )

    run_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return run_id


def update_run(
    run_id,
    row_count,
    status,
    failed_step=None,
    error_message=None,
):

    conn = psycopg2.connect(**get_db_config())

    cur = conn.cursor()

    cur.execute(
        """
        UPDATE pipeline_runs
        SET
            finished_at=%s,
            row_count=%s,
            status=%s,
            failed_step=%s,
            error_message=%s
        WHERE run_id=%s;
        """,
        (
            datetime.now(timezone.utc),
            row_count,
            status,
            failed_step,
            error_message,
            run_id,
        ),
    )

    conn.commit()

    cur.close()
    conn.close()
