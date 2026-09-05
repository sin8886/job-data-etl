import logging
import os

import pandas as pd

from clean import (
    CLEAN_CONFIG,
    clean_company_names,
    clean_salary_estimates,
    drop_configured_columns,
    remove_duplicates,
    replace_invalid_values,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def load_data_chunk(file_path, chunksize=100000):
    """
    Read the CSV in chunks.
    """
    return pd.read_csv(file_path, chunksize=chunksize)


def save_chunk(df, output_path, first_chunk):
    """
    Append data to a temporary file.
    """

    df.to_csv(
        output_path,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False,
    )


def process_chunk(chunk, config):
    """
    Clean one chunk.
    """

    chunk = drop_configured_columns(chunk, config)

    chunk = replace_invalid_values(chunk, config)

    chunk = clean_company_names(chunk, config)

    chunk = clean_salary_estimates(chunk, config)

    return chunk


def run_chunk_clean(input_path, temp_path, chunksize=100000, config=None):
    """
    Stage 1: read, clean, and write chunks to a temporary file.
    """

    cfg = config or CLEAN_CONFIG

    first_chunk = True

    total_input = 0
    total_output = 0

    for chunk in load_data_chunk(input_path, chunksize):

        total_input += len(chunk)

        logger.info("Processing chunk: rows=%d", len(chunk))

        chunk = process_chunk(chunk, cfg)

        # Remove duplicates within the chunk.
        chunk = remove_duplicates(chunk, cfg)

        total_output += len(chunk)

        save_chunk(chunk, temp_path, first_chunk)

        first_chunk = False

    logger.info(
        "Chunk cleaning completed: input=%d output=%d", total_input, total_output
    )


def global_deduplicate(input_path, output_path):
    """
    Stage 2: deduplicate the complete intermediate file.
    """

    logger.info("Starting global deduplication")

    df = pd.read_csv(input_path)

    before = len(df)

    # Business key.
    unique_columns = [
        "Company Name",
        "Job Title",
        "Location",
    ]

    # Use the business key when all fields are available.
    existing_columns = [col for col in unique_columns if col in df.columns]

    if existing_columns:

        df = df.drop_duplicates(subset=existing_columns)

    else:

        df = df.drop_duplicates()

    after = len(df)

    logger.info(
        "Global deduplication completed: before=%d after=%d removed=%d",
        before,
        after,
        before - after,
    )

    # Regenerate job IDs.

    if "job_id" in df.columns:
        df = df.drop(columns=["job_id"])

    df.insert(0, "job_id", range(1, len(df) + 1))

    df.to_csv(output_path, index=False)

    logger.info("Final file generated: %s", output_path)


def run_full_chunk_pipeline(input_path, output_path):

    temp_path = output_path + ".temp.csv"

    # Remove any previous temporary file.
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # Stage 1
    run_chunk_clean(input_path, temp_path)

    # Stage 2
    global_deduplicate(temp_path, output_path)

    # Remove the temporary file.
    if os.path.exists(temp_path):
        os.remove(temp_path)


if __name__ == "__main__":

    input_file = r"D:\桌面\DE\data\raw\DataAnalyst_big.csv"

    output_file = r"D:\桌面\DE\data\clean\jobs_chunk_clean.csv"

    run_full_chunk_pipeline(input_file, output_file)
