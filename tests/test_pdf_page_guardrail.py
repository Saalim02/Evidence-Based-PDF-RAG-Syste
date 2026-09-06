import pytest

from app.services import pdf_service


class FakeDocument:
    def __init__(self, page_count):
        self.page_count = page_count
        self.closed = False

    def __len__(self):
        return self.page_count

    def __iter__(self):
        return iter([])

    def close(self):
        self.closed = True


def test_pdf_at_page_limit_is_allowed(monkeypatch):
    fake_doc = FakeDocument(1400)

    monkeypatch.setattr(
        pdf_service.fitz,
        "open",
        lambda _: fake_doc,
    )

    result = pdf_service.extract_text_from_pdf("test.pdf")

    assert result["total_pages"] == 1400
    assert result["pages"] == []


def test_pdf_above_page_limit_is_blocked(monkeypatch):
    fake_doc = FakeDocument(1401)

    monkeypatch.setattr(
        pdf_service.fitz,
        "open",
        lambda _: fake_doc,
    )

    with pytest.raises(
        ValueError,
        match="maximum allowed page count of 1400 pages",
    ):
        pdf_service.extract_text_from_pdf("test.pdf")

    assert fake_doc.closed is True


def test_pdf_below_page_limit_is_allowed(monkeypatch):
    fake_doc = FakeDocument(1200)

    monkeypatch.setattr(
        pdf_service.fitz,
        "open",
        lambda _: fake_doc,
    )

    result = pdf_service.extract_text_from_pdf("test.pdf")

    assert result["total_pages"] == 1200

def test_malformed_pdf_is_rejected(monkeypatch):
    def fake_open(_):
        raise RuntimeError("cannot open malformed PDF")

    monkeypatch.setattr(
        pdf_service.fitz,
        "open",
        fake_open,
    )

    with pytest.raises(
        ValueError,
        match="Invalid or unreadable PDF",
    ):
        pdf_service.extract_text_from_pdf("malformed.pdf")
