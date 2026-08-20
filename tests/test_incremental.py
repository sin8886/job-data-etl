import pandas as pd

from pipeline import incremental


class FakeCursor:

    def __init__(self, rows):
        self.rows = rows
        self.closed = False

    def execute(self, query):
        self.query = query

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:

    def __init__(self, rows):
        self.cursor_instance = FakeCursor(rows)
        self.closed = False

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def mock_existing_keys(monkeypatch, rows):
    connection = FakeConnection(rows)
    monkeypatch.setattr(incremental.psycopg2, "connect", lambda **kwargs: connection)
    return connection


def test_filter_existing_records_filters_existing_business_key(monkeypatch):

    mock_existing_keys(
        monkeypatch,
        [("Google", "Data Analyst", "New York")],
    )
    df = pd.DataFrame(
        {
            "Company Name": ["Google"],
            "Job Title": ["Data Analyst"],
            "Location": ["New York"],
        }
    )

    result = incremental.filter_existing_records(df)

    assert result.empty


def test_filter_existing_records_keeps_new_business_key(monkeypatch):

    mock_existing_keys(
        monkeypatch,
        [("Google", "Data Analyst", "New York")],
    )
    df = pd.DataFrame(
        {
            "Company Name": ["OpenAI"],
            "Job Title": ["Research Analyst"],
            "Location": ["San Francisco"],
        }
    )

    result = incremental.filter_existing_records(df)

    pd.testing.assert_frame_equal(result, df)


def test_filter_existing_records_normalizes_case_and_whitespace(monkeypatch):

    mock_existing_keys(
        monkeypatch,
        [("Google", "Data Analyst", "New York")],
    )
    df = pd.DataFrame(
        {
            "Company Name": ["  google  "],
            "Job Title": [" data analyst "],
            "Location": [" NEW YORK "],
        }
    )

    result = incremental.filter_existing_records(df)

    assert result.empty


def test_filter_existing_records_uses_case_insensitive_company_identity(monkeypatch):
    mock_existing_keys(
        monkeypatch,
        [("taskrabbit", "Senior Data Analyst", "San Francisco, CA")],
    )
    df = pd.DataFrame(
        {
            "Company Name": ["TaskRabbit"],
            "Job Title": ["Senior Data Analyst"],
            "Location": ["San Francisco, CA"],
        }
    )

    result = incremental.filter_existing_records(df)

    assert result.empty
