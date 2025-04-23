"""Запуск интерфейса Streamlit."""
import asyncio

from pathlib import Path

import streamlit as st

from config import BASEDIR
from start_parser import start_parser
from logger_config import log
from app_exceptions import IndexFileNotExistsError
from utils.common_utils import create_index_md_file
from parser.parser_config import default_strip_tags, default_strip_classes, default_excluded_domains

if __name__ == "__main__":
    def run_app() -> None:
        """Функция для запуска приложения через Streamlit."""
        st.title("Приложение для конвертации html данных страниц в markdown файлы")

        start_urls_input = st.text_area("Введите начальные URL-адреса, "
                                        "например https://example.com/rating/something?page=1 "
                                        "(по одному на строку)", height=150)
        start_urls = [url.strip() for url in start_urls_input.split("\n") if url.strip()]

        only_first_page = st.checkbox("Получить только md указанных страниц", value=False)

        default_dir = BASEDIR / "misc"
        output_directory_input = st.text_input("Введите путь к выходной директории", value=str(default_dir))
        output_directory = Path(output_directory_input)

        css_classes_to_exclude_input = st.text_area("Введите CSS-классы для исключения из результатов",
                                                    value="\n".join(default_strip_classes),
                                                    height=100)
        css_classes_to_exclude = (
            tuple([str(_class).strip()
                   for _class in css_classes_to_exclude_input.split("\n") if _class.strip()]))

        tags_names_to_exclude_input = st.text_area("Введите теги для исключения из результатов",
                                                   value="\n".join(default_strip_tags),
                                                   height=100)

        tags_names_to_exclude = (
            tuple([str(tag_name).strip()
                   for tag_name in tags_names_to_exclude_input.split("\n") if tag_name.strip()]))

        allowed_domains_input = st.text_area(
            "Введите разрешенные домены, например, example.com ",
            height=100,
        )
        allowed_domains = tuple([str(domain).strip() for domain in allowed_domains_input.split("\n") if domain.strip()])

        excluded_domains_input = st.text_area(
            "Введите исключаемые домены (по одному на строку). По умолчанию используются:",
            "\n".join(default_excluded_domains),
            height=150,
        )
        excluded_domains = [domain.strip() for domain in excluded_domains_input.split("\n") if domain.strip()]
        # значения по умолчанию
        if not excluded_domains:
            excluded_domains = default_excluded_domains

        if not css_classes_to_exclude:
            css_classes_to_exclude = default_strip_classes

        if not tags_names_to_exclude:
            tags_names_to_exclude = default_strip_tags

        if not output_directory:
            output_directory = default_dir

        # запуск
        if st.button("Запустить парсинг"):
            if not start_urls:
                st.error("Пожалуйста, введите хотя бы один URL-адрес.")
                return

            if not output_directory.exists():
                try:
                    output_directory.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    st.error(f"Не удалось создать выходную директорию: {e}")
                    return

            for url in start_urls:
                msg = f"Обработка {url}..." if not only_first_page else \
                    f"Обработка {url} (получение md только указанных страниц)..."
                st.info(msg)
                log.info(msg)
                asyncio.run(start_parser(
                    start_url=url,
                    output_directory=output_directory,
                    css_class=css_classes_to_exclude,
                    tag_name=tags_names_to_exclude,
                    allowed_domains=allowed_domains,
                    excluded_domains=excluded_domains,
                    only_first_page=only_first_page,
                ))

            # Создание индексного файла
            try:
                create_index_md_file(output_directory)
                st.success("Парсинг завершен. Список файлов создан..")
            except IndexFileNotExistsError as e:
                log.error("Ошибка при создании индексного файла.")
                log.exception(e)
                st.error("Произошла ошибка при создании индексного файла.")


    if __name__ == "__main__":
        run_app()
