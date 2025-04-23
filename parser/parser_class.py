"""Парсер."""
import re

from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections.abc import Callable, Awaitable

import aiohttp

from bs4 import BeautifulSoup
from aiohttp import ClientSession
from markdownify import markdownify

from logger_config import log
from utils.common_utils import sanitize_filename, save_markdown_file
from parser.parser_config import default_strip_tags, default_strip_classes, default_excluded_domains


class Parser:
    """Класс для парсинга HTML страниц."""

    def __init__(self,
                 start_page_url: str,
                 directory: Path,
                 session: aiohttp.ClientSession,
                 fetch_html: Callable[[ClientSession, str], Awaitable],
                 allowed_domains: tuple[str, ...],
                 excluded_domains: tuple[str, ...] = default_excluded_domains,
                 css_classes: tuple[str, ...] | None = default_strip_classes,
                 tags_names: tuple[str, ...] | None = default_strip_tags,
                 ) -> None:
        """Инициализация парсера."""
        self.start_page_url = start_page_url
        self.directory = directory
        self.css_classes = css_classes
        self.tags_names = tags_names
        self.session = session
        self.fetch_html = fetch_html
        self.allowed_domains = allowed_domains
        self.excluded_domains = excluded_domains

    async def get_start_page_html(self) -> str:
        """Получение HTML-кода стартовой страницы."""
        return await self.fetch_html(self.session, self.start_page_url)

    async def _extract_links(self) -> list[tuple[str, str]]:
        """Извлекает все ссылки со страницы."""
        self.start_page_html = await self.get_start_page_html()
        start_page_soup = BeautifulSoup(self.start_page_html, "html.parser")
        links = []
        for a_tag in start_page_soup.find_all("a", href=True):
            href: str = a_tag["href"]
            full_url: str = urljoin(self.start_page_url, href)
            links.append((full_url, a_tag.get_text(strip=True)))
        return links

    async def filter_links(self) -> list[tuple[str, str]]:
        """Фильтрует ссылки по спискам разрешённых и игнорируемых доменов."""
        filtered_links = []
        extracted_links = await self._extract_links()
        for link, link_text in extracted_links:
            parsed_url = urlparse(link)
            domain = parsed_url.netloc
            if self.excluded_domains and any(excluded_domain in domain for excluded_domain in self.excluded_domains):
                continue
            if self.allowed_domains and not any(allowed_domain in domain for allowed_domain in self.allowed_domains):
                continue
            filtered_links.append((link, link_text))
        return filtered_links

    async def process_page(self, page_link: str) -> None:
        """Обрабатывает одну страницу: сохраняет её содержимое и добавляет в ссылку на INDEX.md."""
        page_link_html = await self.fetch_html(self.session, page_link)
        if not page_link_html:
            log.warning("Url не получен.", url=page_link)
            return

        page_soup = BeautifulSoup(page_link_html, "html.parser")

        # удаление тегов, указанных с css классами в css_classes
        for element in page_soup.find_all(class_=lambda class_: class_ in self.css_classes):
            element.decompose()

        title_tag = page_soup.find("title")
        a_tag_text = title_tag.get_text(strip=True) if title_tag else "Unnamed_Page"
        unique_name = sanitize_filename(a_tag_text)

        log.info(f"Обработка страницы: {unique_name} ({page_link})")

        content = markdownify(str(page_soup), code_language="python",
                              default_title=False,
                              strip=self.tags_names)

        cleaned_content = content.replace(unique_name, "")
        cleaned_content = re.sub(r"\n{2,}", "\n", cleaned_content)

        if not content.strip():
            log.warning(f"Контент страницы {page_link} пуст. Файл не создан.")
            return

        # Создаем markdown файл для страницы
        page_content = f"{cleaned_content}\n\n[[INDEX.md]]"
        save_markdown_file(self.directory, unique_name, page_content)
