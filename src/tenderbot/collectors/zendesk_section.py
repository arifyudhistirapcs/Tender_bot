"""Kolektor artikel pengumuman dari section Zendesk publik."""

from __future__ import annotations

import json

from ..config import Bank
from ..http_client import AccessError, Fetcher
from ..models import Item
from .base import CollectResult, html_to_text


def parse_zendesk_section(json_text: str, bank: Bank) -> list[Item]:
    """Ubah respons Zendesk section menjadi item portal dengan isi detail."""
    try:
        payload = json.loads(json_text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return []

    items: list[Item] = []
    for article in payload.get("articles", []) or []:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title") or "").strip()
        url = str(article.get("html_url") or "").strip()
        if not title or not url:
            continue
        detail_text = html_to_text(str(article.get("body") or ""))[:8000]
        created_at = str(article.get("created_at") or "")
        published = created_at[:10] if len(created_at) >= 10 else None
        items.append(Item(
            bank=bank.name,
            group=bank.group,
            title=title,
            url=url,
            published=published,
            posted=published,
            source_type="portal",
            evidence=detail_text[:300],
            detail_text=detail_text,
        ))
    return items


def collect_zendesk_section(fetcher: Fetcher, bank: Bank, url: str) -> CollectResult:
    """Ambil satu halaman artikel section Zendesk tanpa login."""
    try:
        response = fetcher.fetch(url)
    except AccessError as exc:
        return CollectResult(ok=False, error=exc.reason)
    try:
        json.loads(response.text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return CollectResult(ok=False, error="JSON Zendesk tidak sah")
    return CollectResult(items=parse_zendesk_section(response.text, bank))
