import pandas as pd

from clean import clean_company_names, replace_invalid_values


def test_replace_invalid_values():
    """
    测试无效值替换功能
    -1 是否被替换为空值
    """

    df = pd.DataFrame({
        "age": [20, -1, 30],
        "salary": [5000, -1, 8000]
    })

    result = replace_invalid_values(df)

    # 检查无效值是否被替换
    assert pd.isna(result.loc[1, "age"])
    assert pd.isna(result.loc[1, "salary"])

    # 检查正常数据没有变化
    assert result.loc[0, "age"] == 20
    assert result.loc[2, "salary"] == 8000


def test_clean_company_names():
    """
    测试公司名称清洗功能
    换行后的内容是否被截断
    """

    df = pd.DataFrame({
        "Company Name": [
            "Google\nGoogle LLC",
            "Microsoft\nMicrosoft Corporation",
            "Apple"
        ]
    })

    result = clean_company_names(df)

    # 检查是否只保留第一部分
    assert result.loc[0, "Company Name"] == "Google"
    assert result.loc[1, "Company Name"] == "Microsoft"
    assert result.loc[2, "Company Name"] == "Apple"


def test_clean_company_names_removes_surrounding_whitespace():
    df = pd.DataFrame({"Company Name": ["  TaskRabbit  "]})

    result = clean_company_names(df)

    assert result.loc[0, "Company Name"] == "TaskRabbit"
