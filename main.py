import logging

from pipeline.extract import extract
from pipeline.transform import transform
from pipeline.incremental import filter_existing_records
from pipeline.validate import validate
from pipeline.load import load
from pipeline.report import generate_report

from audit import create_run, update_run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main():

    logger.info("ETL Pipeline Start")

    # 创建一次 pipeline run 记录
    run_id = create_run()

    try:

        # Extract
        raw_path = extract()

        # Transform
        df = transform(raw_path)

        # Incremental Filter
        df = filter_existing_records(df)

        # 没有新增数据，直接结束
        if df.empty:
            logger.info("No new records found. Skip loading.")

            update_run(run_id, 0, "SUCCESS")

            logger.info("ETL Pipeline Finished")

            return

        # Validate
        validate(df)

        # Load（只加载新增数据）
        load(df)

        # Report
        generate_report(df)

        # Audit
        update_run(run_id, len(df), "SUCCESS")

        logger.info("ETL Pipeline Finished")

    except Exception as e:

        logger.exception("ETL Pipeline Failed")

        update_run(run_id, 0, "FAILED")

        raise e


if __name__ == "__main__":
    main()
