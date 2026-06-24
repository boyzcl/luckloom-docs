#!/usr/bin/env python3
"""Validate the LuckLoom static documentation site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

PROJECT_BASE_PATH = "/luckloom-docs/"
ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.lang = ""
        self.title = ""
        self.in_title = False
        self.has_charset = False
        self.has_viewport = False
        self.has_description = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag == "html":
            self.lang = attrs_dict.get("lang", "")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            if attrs_dict.get("charset"):
                self.has_charset = True
            if attrs_dict.get("name", "").lower() == "viewport":
                self.has_viewport = bool(attrs_dict.get("content", "").strip())
            if attrs_dict.get("name", "").lower() == "description":
                self.has_description = bool(attrs_dict.get("content", "").strip())
        elif tag == "a":
            href = attrs_dict.get("href", "").strip()
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def route_exists(path: Path) -> bool:
    if path.is_file():
        return True
    if path.is_dir() and (path / "index.html").is_file():
        return True
    if path.with_suffix(".html").is_file():
        return True
    return False


def resolve_internal_link(page: Path, href: str) -> Path | None:
    parsed = urlparse(href)
    if parsed.scheme in {"http", "https", "mailto", "tel"}:
        return None
    if parsed.netloc:
        return None
    raw_path = unquote(parsed.path)
    if not raw_path:
        return None
    if raw_path.startswith(PROJECT_BASE_PATH):
        return ROOT / raw_path[len(PROJECT_BASE_PATH) :]
    if raw_path.startswith("/"):
        raise ValueError(f"root-relative link must start with {PROJECT_BASE_PATH!r}: {href}")
    return (page.parent / raw_path).resolve()


def validate_page(page: Path) -> list[str]:
    parser = PageParser()
    parser.feed(page.read_text(encoding="utf-8"))

    errors: list[str] = []
    label = page.relative_to(ROOT)

    if not parser.lang:
        errors.append(f"{label}: missing html lang")
    if not parser.has_charset:
        errors.append(f"{label}: missing charset meta")
    if not parser.has_viewport:
        errors.append(f"{label}: missing viewport meta")
    if not parser.title.strip():
        errors.append(f"{label}: missing title")
    if not parser.has_description:
        errors.append(f"{label}: missing meta description")

    for href in parser.links:
        try:
            target = resolve_internal_link(page, href)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")
            continue
        if target is None:
            continue
        try:
            target.relative_to(ROOT)
        except ValueError:
            errors.append(f"{label}: link escapes site root: {href}")
            continue
        if not route_exists(target):
            errors.append(f"{label}: broken internal link: {href}")

    return errors


def main() -> int:
    pages = sorted(ROOT.glob("**/*.html"))
    errors: list[str] = []

    if not pages:
        errors.append("no HTML files found")
    for page in pages:
        errors.extend(validate_page(page))

    if errors:
        print("Static site check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Static site check passed: {len(pages)} HTML files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
