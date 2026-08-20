import pandas as pd
import pytest

from pipeline.validate import validate


def test_validate_raises_when_quality_check_fails():

    empty_df = pd.DataFrame({
        "job_id": pd.Series(dtype="int64")
    })

    with pytest.raises(Exception, match="Quality failed"):
        validate(empty_df)
