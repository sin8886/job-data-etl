import pandas as pd
import pytest

from exceptions import QualityValidationError
from pipeline.validate import validate


def test_validate_raises_when_quality_check_fails():
    empty_df = pd.DataFrame(
        {
            "job_id": pd.Series(dtype="int64"),
        }
    )

    with pytest.raises(QualityValidationError, match="Quality failed"):
        validate(empty_df)
