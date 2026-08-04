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

        "name":[
            "A",
            None,
            "B"
        ]

    })


    result = check_null_rate(
        df,
        threshold=0.5
    )


    assert result["passed"]



def test_unique():

    df = pd.DataFrame({

        "job_id":[1,2,3]

    })


    result = check_unique(
        df,
        "job_id"
    )


    assert result["passed"]