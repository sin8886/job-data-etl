import pandas as pd


def check_row_count(df, min_rows=1):
    """
    检查数据行数
    """

    row_count = len(df)

    result = {
        "check": "row_count",
        "passed": row_count >= min_rows,
        "value": row_count
    }

    return result



def check_null_rate(df, threshold=0.2):
    """
    检查字段空值率
    """

    null_rate = df.isna().mean()

    failed_columns = null_rate[
        null_rate > threshold
    ].index.tolist()


    result = {
        "check": "null_rate",
        "passed": len(failed_columns) == 0,
        "failed_columns": failed_columns,
        "value": null_rate.to_dict()
    }

    return result



def check_unique(df, column):
    """
    检查字段唯一性
    """

    duplicate_count = df[column].duplicated().sum()


    result = {
        "check": "uniqueness",
        "column": column,
        "passed": duplicate_count == 0,
        "duplicates": int(duplicate_count)
    }

    return result