"""Тесты common_utils.py."""
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

import pytest
import aiohttp

from aiohttp.web_exceptions import HTTPOk

from app_exceptions import IndexFileNotExistsError
from utils.common_utils import fetch_html, sanitize_filename, save_markdown_file, create_index_md_file


@pytest.mark.parametrize(("input_text", "expected_output"),
                         [
                             ("test<file>.txt", "test_file_.txt"),
                             ("hello:world?", "hello_world_"),
                             (r"valid\name.txt", "valid_name.txt"),
                             ("no*issues", "no_issues"),
                             ("", ""),
                         ])
def test_sanitize_filename(input_text: str, expected_output: list[tuple[str, str]]) -> None:
    """Тестирование функции очистки имени файла."""
    result = sanitize_filename(input_text)
    assert result == expected_output


@pytest.mark.asyncio
async def test_fetch_html_success() -> None:
    """Тестирование успешного получения HTML-контента."""
    mock_response = AsyncMock()
    mock_response.status = HTTPOk.status_code
    mock_response.text = AsyncMock(return_value="<html>Test</html>")

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None

    with patch("aiohttp.ClientSession.get", return_value=mock_context):
        async with aiohttp.ClientSession() as session:
            result = await fetch_html(session, "http://test.com")

    assert result == "<html>Test</html>"


@pytest.mark.asyncio
async def test_fetch_html_non_200_status() -> None:
    """Тестирование получения страницы с неуспешным статус-кодом."""
    mock_response = AsyncMock()
    mock_response.status = 404

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None

    with patch("aiohttp.ClientSession.get", return_value=mock_context):
        async with aiohttp.ClientSession() as session:
            result = await fetch_html(session, "http://test.com")
        assert result is None


@pytest.mark.asyncio
async def test_fetch_html_connection_error() -> None:
    """Тестирование ошибки подключения при получении HTML."""
    mock_context = AsyncMock()
    mock_context.__aenter__.side_effect = aiohttp.ClientConnectorError(
        connection_key=Mock(), os_error=OSError("Connection failed"),
    )
    mock_context.__aexit__.return_value = None

    with patch("aiohttp.ClientSession.get", return_value=mock_context):
        async with aiohttp.ClientSession() as session:
            result = await fetch_html(session, "http://test.com")
        assert result is None


def test_save_markdown_file(tmp_path: Path) -> None:
    """Тестирование сохранения markdown файла."""
    content = "# Test Content"
    filename = "test_file"
    save_markdown_file(tmp_path, filename, content)

    file_path = tmp_path / f"{filename}.md"
    assert file_path.exists()
    assert file_path.read_text(encoding="utf-8") == content


def test_create_index_md_file(tmp_path: Path) -> None:
    """Тестирование создания INDEX.md файла."""
    (tmp_path / "file1.md").write_text("Content 1")
    (tmp_path / "file2.md").write_text("Content 2")

    create_index_md_file(tmp_path)

    index_file = tmp_path / "INDEX.md"
    assert index_file.exists()


def test_create_index_md_file_nonexistent_directory() -> None:
    """Тестирование создания INDEX.md в несуществующей директории."""
    non_existent_path = Path("non_existent_dir")
    with pytest.raises(IndexFileNotExistsError) as exc_info:
        create_index_md_file(non_existent_path)
    assert str(exc_info.value) == f"Указанный путь не существует или не является директорией: {non_existent_path}"


def test_create_index_md_file_not_directory(tmp_path: Path) -> None:
    """Тестирование создания INDEX.md в пути, который не является директорией."""
    file_path = tmp_path / "not_a_dir.txt"
    file_path.touch()

    with pytest.raises(IndexFileNotExistsError) as exc_info:
        create_index_md_file(file_path)
    assert str(exc_info.value) == f"Указанный путь не существует или не является директорией: {file_path}"
