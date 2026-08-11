import argparse
import logging

from pipeline.extract import extract
from pipeline.transform import transform
from pipeline.incremental import filter_existing_records
from pipeline.validate import validate
from pipeline.load import load
from pipeline.report import generate_report
from pipeline.backfill import run_backfill

from audit import create_run, update_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser(description="ETL Pipeline")

    parser.add_argument(
        "--backfill",
        type=str,
        help="Path to a historical CSV file for backfill.",
    )

    args = parser.parse_args()

    logger.info("ETL Pipeline Start")

    # 创建一次 Pipeline Run
    run_id = create_run("backfill" if args.backfill else "incremental")

    try:

        # ==========================================
        # Backfill Mode
        # ==========================================
        if args.backfill:

            logger.info("Running Backfill Pipeline")

            row_count = run_backfill(args.backfill)

            update_run(run_id, row_count, "SUCCESS")

            logger.info("Backfill Finished")

            return

        # ==========================================
        # Normal Incremental Pipeline
        # ==========================================

        # Extract
        raw_path = extract()

        # Transform
        df = transform(raw_path)

        # Incremental Filter
        df = filter_existing_records(df)

        # 没有新增数据
        if df.empty:

            logger.info("No new records found. Skip loading.")

            update_run(run_id, 0, "SUCCESS")

            logger.info("ETL Pipeline Finished")

            return

        # Validate
        validate(df)

        # Load
        load(df)

        # Report
        generate_report(df)

        # Audit
        update_run(run_id, len(df), "SUCCESS")

        logger.info("ETL Pipeline Finished")

    except Exception:

        logger.exception("ETL Pipeline Failed")

        update_run(run_id, 0, "FAILED")

        raise


if __name__ == "__main__":
    main()
