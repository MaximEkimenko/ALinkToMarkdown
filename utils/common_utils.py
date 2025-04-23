"""Общие утилиты приложения."""
import re

from pathlib import Path

import aiohttp

from aiohttp.web_exceptions import HTTPOk

from logger_config import log
from app_exceptions import IndexFileNotExistsError


def sanitize_filename(text: str) -> str:
    """Очищает название файла от недопустимых символов."""
    return re.sub(r'[<>:"/\\|?*]', "_", text)


async def fetch_html(session: aiohttp.ClientSession, url: str) -> str | None:
    """Получение HTML-контент страницы по URL."""
    try:
        async with session.get(url) as response:
            if response.status != HTTPOk.status_code:
                log.warning(f"Страница {url} вернула статус {response.status}. Переход к следующей странице.")
                return None
            return await response.text()
    except aiohttp.ClientConnectorError:
        log.error("Не удалось подключиться к {url}. Переход к следующей странице.", url=url)


def save_markdown_file(directory: Path, filename: str, content: str) -> None:
    """Сохраняет содержимое в markdown файл."""
    filepath: Path = directory / f"{filename}.md"
    filepath.write_text(content, encoding="utf-8")


def create_index_md_file(directory: Path, index_file_name: str = "INDEX.md") -> None:
    """Создает файл INDEX.md в указанной директории с перечислением всех файлов в формате Obsidian-ссылок."""
    if not directory.exists() or not directory.is_dir():
        msg = f"Указанный путь не существует или не является директорией: {directory}"
        raise IndexFileNotExistsError(msg)

    files = list(directory.iterdir())
    files = [file for file in files if file.is_file()]

    index_content_list = [f"# Список файлов папки {directory.name} \n"]
    for i, file in enumerate(files, start=1):
        file_name = file.name
        obsidian_link = f"[[{file_name}]]"
        index_content_list.append(f"{i}. {obsidian_link}\n")

    index_content = "".join(index_content_list)

    index_file_path = directory / index_file_name
    with index_file_path.open("w", encoding="utf-8") as index_file:
        index_file.write(index_content)

    log.success(f"Файл {index_file_name} успешно создан в директории {directory}.")
