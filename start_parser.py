"""Запуск парсера."""
from pathlib import Path

import aiohttp

from utils.common_utils import fetch_html

# from config import activate_link
from parser.parser_class import Parser


async def start_parser(start_url: str,
                       output_directory: Path,
                       allowed_domains: tuple[str, ...],
                       excluded_domains: tuple[str, ...] | None = None,
                       css_class: str | None = None,
                       tag_name: str | None = None,
                       only_first_page: bool = False,  # получение markdown только указанных страниц
                       ) -> None:
    """Запуск парсера."""
    output_directory.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        parser = Parser(start_page_url=start_url,
                        directory=output_directory,
                        fetch_html=fetch_html,
                        session=session,
                        allowed_domains=allowed_domains,
                        excluded_domains=excluded_domains,
                        css_classes=css_class,
                        tags_names=tag_name,
                        )
        if only_first_page is True:
            await parser.process_page(page_link=start_url)
            return

        links = await parser.filter_links()
        for link, _ in links:
            await parser.process_page(page_link=link)
