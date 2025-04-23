"""Тесты parser_class.py."""
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import aiohttp

from parser.parser_class import Parser


@pytest.fixture
def mock_session() -> AsyncMock:
    """Mock для объекта aiohttp.ClientSession."""
    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.fixture
def parser(mock_session: AsyncMock, tmp_path: Path) -> Parser:
    """Фикстура для создания объекта Parser."""
    start_page_url = "https://example.com"
    directory = tmp_path
    fetch_html = AsyncMock()
    allowed_domains = ("example.com",)
    return Parser(
        start_page_url=start_page_url,
        directory=directory,
        session=mock_session,
        fetch_html=fetch_html,
        allowed_domains=allowed_domains,
    )


@pytest.mark.asyncio
async def test_get_start_page_html(parser: Parser) -> None:
    """Тестирование получения HTML-кода стартовой страницы."""
    html_content = "<html><body><h1>Test</h1></body></html>"
    parser.fetch_html.return_value = html_content
    result = await parser.get_start_page_html()
    assert result == html_content


@pytest.mark.asyncio
async def test_extract_links(parser: Parser) -> None:
    """Тестирование извлечения ссылок."""
    html_content = """
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://anotherdomain.com/page2">Page 2</a>
        </body>
    </html>
    """
    parser.fetch_html.return_value = html_content
    links = await parser._extract_links()
    expected_links = [
        ("https://example.com/page1", "Page 1"),
        ("https://anotherdomain.com/page2", "Page 2"),
    ]
    assert links == expected_links


@pytest.mark.asyncio
async def test_filter_links(parser: Parser) -> None:
    """Тестирование фильтрации ссылок."""
    parser.allowed_domains = ("example.com",)
    parser.excluded_domains = ("anotherdomain.com",)
    links = [
        ("https://example.com/page1", "Page 1"),
        ("https://anotherdomain.com/page2", "Page 2"),
    ]
    with patch.object(parser, "_extract_links", return_value=links):
        filtered_links = await parser.filter_links()
    expected_filtered_links = [("https://example.com/page1", "Page 1")]
    assert filtered_links == expected_filtered_links


@pytest.mark.asyncio
async def test_process_page(parser: Parser, tmp_path: Path) -> None:
    """Тестирование обработки страницы."""
    page_link = "https://example.com/page1"
    # TODO добавить удаляемые теги и классы
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <p class="remove-me">This will be removed</p>
            <p>This is some content</p>
        </body>
    </html>
    """
    parser.fetch_html.return_value = html_content
    parser.css_classes = ("remove-me",)

    await parser.process_page(page_link)

    from utils.common_utils import sanitize_filename
    expected_filename = sanitize_filename("Test Page") + ".md"
    file_path = tmp_path / expected_filename

    # Проверяем, что файл был создан
    assert file_path.exists(), f"Файл {file_path} не был создан"

    # Проверяем содержимое файла
    with file_path.open(mode="r", encoding="utf-8") as f:
        content = f.read()
    assert "This is some content" in content
    assert "[[INDEX.md]]" in content
    assert "This will be removed" not in content


@pytest.mark.asyncio
async def test_process_page_empty_content(parser: Parser, tmp_path: Path) -> None:
    """Тестирование обработки страницы с пустым содержимым и не созданного файла результатов md."""
    page_link = "https://example.com/page1"
    html_content = "<html><body></body></html>"
    parser.fetch_html.return_value = html_content

    await parser.process_page(page_link)

    file_path = tmp_path / "Unnamed_Page.md"
    assert not file_path.exists()
