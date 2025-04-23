"""Конфигурация парсера."""
# игнорируемые домены по умолчанию
default_excluded_domains = (
    "google.com",
    "facebook.com",
    "youtube.com",
    "github.com",
    "t.me",
    "linkedin.com",
    "instagram.com",
    "twitter.com",
)

# имена тегов, которые будут удалены при парсинге по умолчанию
default_strip_tags = (
    "img",
    "footer",
    "nav",
    "label",
    "input",
    "script",
)

# css классы, которые будут удалены при парсинге по умолчанию
default_strip_classes = (
    "fs-2 me-2 nav-link",
    "modal-title fs-5",
    "nav-link", "btn",
    "col-form-label",
)
