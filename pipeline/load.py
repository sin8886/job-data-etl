import tempfile

from load_to_postgres import (
    main as load_main,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
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
        raise Exception("Database load failed")
