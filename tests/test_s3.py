from unittest.mock import MagicMock, patch

import pytest

from pipeline.storage.s3 import (
    get_bucket_name,
    get_s3_client,
    upload_file,
)


def test_get_bucket_name_success(monkeypatch):
    """Should return the configured S3 bucket name."""
    monkeypatch.setenv(
        "S3_BUCKET_NAME",
        "test-bucket",
    )

    assert get_bucket_name() == "test-bucket"


def test_get_bucket_name_missing(monkeypatch):
    """Should raise an error when bucket name is missing."""
    monkeypatch.delenv(
        "S3_BUCKET_NAME",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="S3_BUCKET_NAME is not configured",
    ):
        get_bucket_name()


@patch("pipeline.storage.s3.boto3.client")
def test_get_s3_client_success(mock_boto_client, monkeypatch):
    """Should create an S3 client using the configured AWS region."""
    monkeypatch.setenv(
        "AWS_REGION",
        "ap-southeast-2",
    )

    get_s3_client()

    mock_boto_client.assert_called_once_with(
        "s3",
        region_name="ap-southeast-2",
    )


def test_get_s3_client_missing_region(monkeypatch):
    """Should raise an error when AWS region is missing."""
    monkeypatch.delenv(
        "AWS_REGION",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="AWS_REGION is not configured",
    ):
        get_s3_client()


@patch("pipeline.storage.s3.get_s3_client")
def test_upload_file_success(
    mock_get_s3_client,
    monkeypatch,
    tmp_path,
):
    """Should upload an existing local file using the S3 client."""

    monkeypatch.setenv(
        "S3_BUCKET_NAME",
        "test-bucket",
    )

    test_file = tmp_path / "test.csv"
    test_file.write_text(
        "id,name\n1,test\n",
        encoding="utf-8",
    )

    mock_s3 = MagicMock()
    mock_get_s3_client.return_value = mock_s3

    upload_file(
        test_file,
        "raw/test.csv",
    )

    mock_s3.upload_file.assert_called_once_with(
        str(test_file),
        "test-bucket",
        "raw/test.csv",
    )


def test_upload_file_missing_local_file(tmp_path):
    """Should raise an error when the local file does not exist."""

    missing_file = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Local file not found",
    ):
        upload_file(
            missing_file,
            "raw/missing.csv",
        )
