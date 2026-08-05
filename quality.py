import pandas as pd


def check_row_count(df, min_rows=1):
    """
    检查数据行数
    """

    row_count = len(df)

    result = {
        "check": "row_count",
        "passed": bool(row_count >= min_rows),
        "value": row_count,
    }

    return result


def check_null_rate(df, threshold=0.2):
    """
    检查关键字段空值率

    只检查影响业务的数据字段，
    普通描述字段允许存在缺失。
    """

    null_rate = df.isna().mean()

    # ETL关键字段
    critical_columns = ["Job Title", "Company Name", "Location", "Industry"]

    failed_columns = []

    for column in critical_columns:
        if column in null_rate:
            if null_rate[column] > threshold:
                failed_columns.append(column)

    result = {
        "check": "null_rate",
        "passed": len(failed_columns) == 0,
        "failed_columns": failed_columns,
        "threshold": threshold,
        "value": {
            col: float(null_rate[col]) for col in critical_columns if col in null_rate
        },
    }

    return result


def check_unique(df, column):
    """
    检查字段唯一性

    例如：
    job_id
    company_id

    """

    if column not in df.columns:
        return {
            "check": "uniqueness",
            "column": column,
            "passed": False,
            "error": "column not found",
        }

    duplicate_count = df[column].duplicated().sum()

    result = {
        "check": "uniqueness",
        "column": column,
        "passed": bool(duplicate_count == 0),
        "duplicates": int(duplicate_count),
    }

    return result
