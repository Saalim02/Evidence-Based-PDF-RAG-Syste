import asyncio

import pytest
from fastapi import HTTPException

from app.utils import file_handler


class FakeUploadFile:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.filename = "test.pdf"
        self.read_sizes = []

    async def read(self, size=-1):
        self.read_sizes.append(size)

        try:
            return next(self.chunks)
        except StopIteration:
            return b""


def run_async(coroutine):
    return asyncio.run(coroutine)


def test_file_at_size_limit_is_allowed(tmp_path, monkeypatch):
    monkeypatch.setattr(
        file_handler,
        "UPLOAD_DIR",
        tmp_path,
    )

    chunk_size = 1024 * 1024
    chunks = [b"x" * chunk_size] * 200

    fake_file = FakeUploadFile(chunks)

    result = run_async(
        file_handler.save_uploaded_file(fake_file)
    )

    assert result[0] == "test.pdf"
    assert result[2] == 200.0

    saved_path = tmp_path / result[1].split("/")[-1]

    assert saved_path.exists()
    assert saved_path.stat().st_size == 200 * 1024 * 1024

    assert all(
        size == chunk_size
        for size in fake_file.read_sizes
        if size != -1
    )


def test_file_over_size_limit_is_blocked_and_deleted(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        file_handler,
        "UPLOAD_DIR",
        tmp_path,
    )

    chunk_size = 1024 * 1024
    chunks = [b"x" * chunk_size] * 201

    fake_file = FakeUploadFile(chunks)

    with pytest.raises(
        HTTPException,
        match="File exceeds 200 MB limit",
    ):
        run_async(
            file_handler.save_uploaded_file(fake_file)
        )

    assert list(tmp_path.iterdir()) == []

    assert all(
        size == chunk_size
        for size in fake_file.read_sizes
        if size != -1
    )
