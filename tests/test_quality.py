import pandas as pd

from quality import (
    check_row_count,
    check_null_rate,
    check_unique
)



def test_row_count():

    df = pd.DataFrame({
        "id":[1,2,3]
    })

    result = check_row_count(df)

    assert result["passed"]



def test_null_rate():

    df = pd.DataFrame({

        "Job Title":[
            "A",
            None,
            "B",
            "C"
        ]

    })


    result = check_null_rate(
        df,
        threshold=0.5
    )


    assert result["passed"]
    assert result["value"]["Job Title"] == 0.25



def test_unique():

    df = pd.DataFrame({

        "job_id":[1,2,3]

    })


    result = check_unique(
        df,
        "job_id"
    )


    assert result["passed"]


def test_row_count_fails_below_minimum():

    df = pd.DataFrame({
        "id": [1]
    })

    result = check_row_count(df, min_rows=2)

    assert not result["passed"]
    assert result["value"] == 1


def test_null_rate_fails_for_critical_column():

    df = pd.DataFrame({
        "Job Title": ["Data Analyst", None]
    })

    result = check_null_rate(df, threshold=0.2)

    assert not result["passed"]
    assert result["failed_columns"] == ["Job Title"]


def test_unique_fails_when_job_id_is_duplicated():

    df = pd.DataFrame({
        "job_id": [1, 1, 2]
    })

    result = check_unique(df, "job_id")

    assert not result["passed"]
    assert result["duplicates"] == 1
