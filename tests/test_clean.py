import pandas as pd

from clean import clean_company_names, replace_invalid_values


def test_replace_invalid_values():
    """
    Test invalid-value replacement.
    Verify that -1 is replaced with a null value.
    """

    df = pd.DataFrame({"age": [20, -1, 30], "salary": [5000, -1, 8000]})

    result = replace_invalid_values(df)

    # Verify that invalid values were replaced.
    assert pd.isna(result.loc[1, "age"])
    assert pd.isna(result.loc[1, "salary"])

    # Verify that valid data is unchanged.
    assert result.loc[0, "age"] == 20
    assert result.loc[2, "salary"] == 8000


def test_clean_company_names():
    """
    Test company-name cleaning.
    Verify that content after a line break is removed.
    """

    df = pd.DataFrame(
        {
            "Company Name": [
                "Google\nGoogle LLC",
                "Microsoft\nMicrosoft Corporation",
                "Apple",
            ]
        }
    )

    result = clean_company_names(df)

    # Verify that only the first segment is retained.
    assert result.loc[0, "Company Name"] == "Google"
    assert result.loc[1, "Company Name"] == "Microsoft"
    assert result.loc[2, "Company Name"] == "Apple"


def test_clean_company_names_removes_surrounding_whitespace():
    df = pd.DataFrame({"Company Name": ["  TaskRabbit  "]})

    result = clean_company_names(df)

    assert result.loc[0, "Company Name"] == "TaskRabbit"
