def check_row_count(df, min_rows=1):
    """Check the number of rows in the data frame."""

    row_count = len(df)

    result = {
        "check": "row_count",
        "passed": bool(row_count >= min_rows),
        "value": row_count,
    }

    return result


def check_null_rate(df, threshold=0.2):
    """Check null rates for fields that affect business processing."""

    null_rate = df.isna().mean()

    # Critical ETL fields
    critical_columns = ["Job Title", "Company Name", "Location", "Industry"]

    failed_columns = []

    for column in critical_columns:
        if column in null_rate and null_rate[column] > threshold:
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
    """Check whether the requested field contains duplicate values."""

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
