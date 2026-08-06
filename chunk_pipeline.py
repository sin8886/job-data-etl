import logging
import os

import pandas as pd

from clean import (
    CLEAN_CONFIG,
    drop_configured_columns,
    replace_invalid_values,
    clean_company_names,
    clean_salary_estimates,
    remove_duplicates,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def load_data_chunk(file_path, chunksize=100000):
    """
    分块读取CSV
    """
    return pd.read_csv(file_path, chunksize=chunksize)


def save_chunk(df, output_path, first_chunk):
    """
    追加写入临时文件
    """

    df.to_csv(
        output_path,
        mode="w" if first_chunk else "a",
        header=first_chunk,
        index=False,
    )


def process_chunk(chunk, config):
    """
    单个chunk清洗
    """

    chunk = drop_configured_columns(chunk, config)

    chunk = replace_invalid_values(chunk, config)

    chunk = clean_company_names(chunk, config)

    chunk = clean_salary_estimates(chunk, config)

    return chunk


def run_chunk_clean(input_path, temp_path, chunksize=100000, config=None):
    """
    第一阶段：
    chunk读取 + 清洗 + 写临时文件
    """

    cfg = config or CLEAN_CONFIG

    first_chunk = True

    total_input = 0
    total_output = 0

    for chunk in load_data_chunk(input_path, chunksize):

        total_input += len(chunk)

        logger.info("处理chunk: rows=%d", len(chunk))

        chunk = process_chunk(chunk, cfg)

        # chunk内部简单去重
        chunk = remove_duplicates(chunk, cfg)

        total_output += len(chunk)

        save_chunk(chunk, temp_path, first_chunk)

        first_chunk = False

    logger.info("Chunk清洗完成: input=%d output=%d", total_input, total_output)


def global_deduplicate(input_path, output_path):
    """
    第二阶段：
    全局去重
    """

    logger.info("开始全局去重")

    df = pd.read_csv(input_path)

    before = len(df)

    # 业务唯一键
    unique_columns = [
        "Company Name",
        "Job Title",
        "Location",
    ]

    # 如果字段存在，按业务字段去重
    existing_columns = [col for col in unique_columns if col in df.columns]

    if existing_columns:

        df = df.drop_duplicates(subset=existing_columns)

    else:

        df = df.drop_duplicates()

    after = len(df)

    logger.info(
        "Global dedup完成: before=%d after=%d removed=%d", before, after, before - after
    )

    # 重新生成job_id

    if "job_id" in df.columns:
        df = df.drop(columns=["job_id"])

    df.insert(0, "job_id", range(1, len(df) + 1))

    df.to_csv(output_path, index=False)

    logger.info("最终文件生成: %s", output_path)


def run_full_chunk_pipeline(input_path, output_path):

    temp_path = output_path + ".temp.csv"

    # 删除旧临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)

    # Stage 1
    run_chunk_clean(input_path, temp_path)

    # Stage 2
    global_deduplicate(temp_path, output_path)

    # 删除临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)


if __name__ == "__main__":

    input_file = r"D:\桌面\DE\data\raw\DataAnalyst_big.csv"

    output_file = r"D:\桌面\DE\data\clean\jobs_chunk_clean.csv"

    run_full_chunk_pipeline(input_file, output_file)
