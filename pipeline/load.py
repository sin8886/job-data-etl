import tempfile

from exceptions import DatabaseLoadError
from load_to_postgres import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)
from load_to_postgres import (
    main as load_main,
)


def load(df):
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".csv",
        delete=False,
        newline="",
        encoding="utf-8",
    ) as tmp:
        df.to_csv(tmp.name, index=False)
        csv_path = tmp.name

    code = load_main(
        csv_path,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        DB_HOST,
        DB_PORT,
    )

    if code != 0:
        raise DatabaseLoadError(f"Database load failed with exit code {code}")
