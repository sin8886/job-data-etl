from exceptions import QualityValidationError
from quality import check_null_rate, check_row_count, check_unique


def validate(df):
    results = []

    results.append(check_row_count(df))
    results.append(check_null_rate(df))

    if "job_id" in df.columns:
        results.append(check_unique(df, "job_id"))

    for result in results:
        if not result["passed"]:
            raise QualityValidationError(f"Quality failed: {result}")

    return True
