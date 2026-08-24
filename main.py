import argparse
import logging
import os

from audit import create_run, update_run
from pipeline.backfill import run_backfill
from pipeline.extract import extract
from pipeline.incremental import filter_existing_records
from pipeline.load import load
from pipeline.report import generate_report
from pipeline.retry import retry
from pipeline.transform import transform
from pipeline.validate import validate

# ==========================================
# Logging Configuration
# ==========================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            "logs/pipeline.log",
            mode="a",
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
    force=True,
)

logger = logging.getLogger(__name__)


def main():

    parser = argparse.ArgumentParser(description="ETL Pipeline")

    parser.add_argument(
        "--backfill",
        type=str,
        help="Path to a historical CSV file for backfill.",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Path to an input CSV file for the incremental pipeline.",
    )
    args = parser.parse_args()

    logger.info("ETL Pipeline Start")

    # 创建一次 Pipeline Run
    run_id = create_run("backfill" if args.backfill else "incremental")

    current_step = "UNKNOWN"
    row_count = 0

    try:

        # ==========================================
        # Backfill Mode
        # ==========================================

        if args.backfill:

            current_step = "BACKFILL"

            logger.info("Running Backfill Pipeline")

            row_count = run_backfill(args.backfill)

            update_run(
                run_id,
                row_count,
                "SUCCESS",
            )

            logger.info("Backfill Finished")

            return

        # ==========================================
        # Normal Incremental Pipeline
        # ==========================================

        # ------------------------------------------
        # Extract
        # ------------------------------------------

        current_step = "EXTRACT"

        logger.info("Step: %s", current_step)

        raw_path = extract(args.input)

        logger.info("Extract Finished")

        # ------------------------------------------
        # Transform
        # ------------------------------------------

        current_step = "TRANSFORM"

        logger.info("Step: %s", current_step)

        df = transform(raw_path)

        logger.info("Transform Finished")

        # ------------------------------------------
        # Incremental Filter
        # ------------------------------------------

        current_step = "INCREMENTAL"

        logger.info("Step: %s", current_step)

        df = filter_existing_records(df)

        logger.info(
            "Incremental Filter Finished. New rows: %d",
            len(df),
        )

        # ------------------------------------------
        # No new records
        # ------------------------------------------

        if df.empty:

            logger.info("No new records found. Skip loading.")

            update_run(
                run_id,
                0,
                "SUCCESS",
            )

            logger.info("ETL Pipeline Finished")

            return

        # ------------------------------------------
        # Validate
        # ------------------------------------------

        current_step = "VALIDATE"

        logger.info("Step: %s", current_step)

        validate(df)

        logger.info("Validation Finished")

        # ------------------------------------------
        # Load with Retry
        # ------------------------------------------

        current_step = "LOAD"

        logger.info("Step: %s", current_step)

        retry(
            load,
            df,
            max_retries=3,
            base_delay=2,
        )

        logger.info("Load Finished")

        # ------------------------------------------
        # Report
        # ------------------------------------------

        current_step = "REPORT"

        logger.info("Step: %s", current_step)

        generate_report(df)

        logger.info("Report Finished")

        # ------------------------------------------
        # Audit Success
        # ------------------------------------------

        row_count = len(df)

        update_run(
            run_id,
            row_count,
            "SUCCESS",
        )

        logger.info("ETL Pipeline Finished")

    except Exception as e:

        logger.exception(
            "ETL Pipeline Failed at step: %s",
            current_step,
        )

        update_run(
            run_id,
            row_count,
            "FAILED",
            failed_step=current_step,
            error_message=str(e),
        )

        raise


if __name__ == "__main__":
    main()
