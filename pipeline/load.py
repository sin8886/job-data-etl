from load_to_postgres import (
    main as load_main,
    CSV_PATH,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
)


def load():

    code = load_main(CSV_PATH, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)

    if code != 0:

        raise Exception("Database load failed")
