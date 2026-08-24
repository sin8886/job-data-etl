from pipeline.load import load
from pipeline.report import generate_report
from pipeline.transform import transform
from pipeline.validate import validate


def run_backfill(input_path):
    """
    Run a historical backfill.

    Backfill reuses the existing ETL pipeline but skips
    incremental duplicate filtering. It is intended to
    reload historical datasets using the existing UPSERT
    logic in the database loader.

    Parameters
    ----------
    input_path : str
        Path to a historical CSV file.

    Returns
    -------
    int
        Number of processed rows.
    """

    # Transform
    df = transform(input_path)

    # Validate
    validate(df)

    # Load (UPSERT)
    load(df)

    # Report
    generate_report(df)

    return len(df)
