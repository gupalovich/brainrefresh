import re

from django.utils.text import slugify
from transliterate import translit


def get_unique_slug(cls, field: str) -> str:
    field = translit(field, "ru", reversed=True)  # It'll fix ru unicode titles
    slug = slugify(field)
    unique_slug = slug
    num = 1
    while cls.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{num}"
        num += 1
    return unique_slug


def capitalize_str(s: str) -> str:
    return " ".join([w.capitalize() for w in s.split(" ")]).strip()


def capitalize_slug(slug: str) -> str:
    return re.sub(
        r"\d", "", " ".join([w.capitalize() for w in slug.split("-")])
    ).strip()
