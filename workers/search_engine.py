"""
Search Engine — multi-provider URL discovery.
Supports: SerpAPI, Google Custom Search, Bing, DuckDuckGo (free fallback).
Auto-selects best available provider.
"""
import asyncio
import uuid
from typing import List, Optional
from urllib.parse import quote_plus, urlparse

import aiohttp
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchProvider:
    """Base class for search providers."""

    async def search(self, query: str, max_results: int) -> List[dict]:
        raise NotImplementedError


class SerpAPIProvider(SearchProvider):
    """SerpAPI — supports Google, Bing, etc."""
    BASE = "https://serpapi.com/search"

    async def search(self, query: str, max_results: int) -> List[dict]:
        params = {
            "q":       query,
            "api_key": settings.SERPAPI_KEY,
            "engine":  "google",
            "num":     min(max_results, 100),
            "hl":      "en",
            "gl":      "us",
        }
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.BASE, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()

        results = []
        for i, item in enumerate(data.get("organic_results", []), 1):
            url = item.get("link", "")
            if url and self._is_valid_url(url):
                results.append({
                    "url":     url,
                    "title":   item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "rank":    i,
                    "domain":  urlparse(url).netloc,
                })
            if len(results) >= max_results:
                break
        return results

    def _is_valid_url(self, url: str) -> bool:
        try:
            p = urlparse(url)
            return p.scheme in ("http", "https") and bool(p.netloc)
        except Exception:
            return False


class GoogleCSEProvider(SearchProvider):
    """Google Custom Search Engine — free tier: 100 queries/day."""
    BASE = "https://www.googleapis.com/customsearch/v1"

    async def search(self, query: str, max_results: int) -> List[dict]:
        results = []
        # CSE returns max 10 per page; paginate up to 30
        for start in range(1, min(max_results, 30) + 1, 10):
            params = {
                "key":   settings.GOOGLE_CSE_KEY,
                "cx":    settings.GOOGLE_CSE_ID,
                "q":     query,
                "start": start,
                "num":   min(10, max_results - len(results)),
            }
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.BASE, params=params) as resp:
                    if resp.status != 200:
                        break
                    data = await resp.json()

            for i, item in enumerate(data.get("items", []), start):
                url = item.get("link", "")
                if url:
                    results.append({
                        "url":     url,
                        "title":   item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "rank":    i,
                        "domain":  urlparse(url).netloc,
                    })
            if len(results) >= max_results:
                break
        return results[:max_results]


class BingProvider(SearchProvider):
    """Bing Web Search API."""
    BASE = "https://api.bing.microsoft.com/v7.0/search"

    async def search(self, query: str, max_results: int) -> List[dict]:
        headers = {"Ocp-Apim-Subscription-Key": settings.BING_API_KEY}
        params  = {"q": query, "count": min(max_results, 50), "mkt": "en-US"}
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.BASE, headers=headers, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()

        results = []
        for i, item in enumerate(data.get("webPages", {}).get("value", []), 1):
            url = item.get("url", "")
            if url:
                results.append({
                    "url":     url,
                    "title":   item.get("name", ""),
                    "snippet": item.get("snippet", ""),
                    "rank":    i,
                    "domain":  urlparse(url).netloc,
                })
        return results[:max_results]


class DuckDuckGoProvider(SearchProvider):
    """
    DuckDuckGo HTML scraping — free, no API key required.
    Fallback provider. Returns up to 20 results reliably.
    """
    BASE = "https://html.duckduckgo.com/html/"

    async def search(self, query: str, max_results: int) -> List[dict]:
        import re
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        data_payload = {"q": query, "b": ""}
        timeout = aiohttp.ClientTimeout(total=20)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.BASE, data=data_payload, headers=headers) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()

        from bs4 import BeautifulSoup
        soup    = BeautifulSoup(html, "html.parser")
        results = []

        for i, result in enumerate(soup.select(".result__body"), 1):
            link  = result.select_one(".result__a")
            snip  = result.select_one(".result__snippet")
            if not link:
                continue
            href = link.get("href", "")
            # DDG wraps URLs in a redirect — extract real URL
            if "uddg=" in href:
                from urllib.parse import parse_qs, urlparse as up
                qs  = parse_qs(up(href).query)
                url = qs.get("uddg", [href])[0]
            else:
                url = href
            if url.startswith("http"):
                results.append({
                    "url":     url,
                    "title":   link.get_text(strip=True),
                    "snippet": snip.get_text(strip=True) if snip else "",
                    "rank":    i,
                    "domain":  urlparse(url).netloc,
                })
            if len(results) >= max_results:
                break

        return results


# ─── Orchestrator ─────────────────────────────────────────────────────────────

class SearchOrchestrator:
    """
    Picks the best available search provider.
    Deduplicates results by domain (max 3 per domain).
    """

    def _get_provider(self, preferred: str = "auto") -> SearchProvider:
        if preferred == "serpapi" and settings.SERPAPI_KEY:
            return SerpAPIProvider()
        if preferred == "google" and settings.GOOGLE_CSE_KEY:
            return GoogleCSEProvider()
        if preferred == "bing" and settings.BING_API_KEY:
            return BingProvider()
        if preferred == "duckduckgo":
            return DuckDuckGoProvider()

        # Auto: pick first available
        if settings.SERPAPI_KEY:
            return SerpAPIProvider()
        if settings.GOOGLE_CSE_KEY and settings.GOOGLE_CSE_ID:
            return GoogleCSEProvider()
        if settings.BING_API_KEY:
            return BingProvider()

        logger.warning("No paid search API configured — using DuckDuckGo fallback")
        return DuckDuckGoProvider()

    async def search(self, query: str, max_results: int = 30, engine: str = "auto") -> List[dict]:
        provider = self._get_provider(engine)
        logger.info(f"Search '{query}' via {provider.__class__.__name__}")

        results = await provider.search(query, max_results)

        # Deduplicate by domain (keep top 3 per domain)
        domain_count: dict = {}
        deduped = []
        for r in results:
            domain = r.get("domain", "")
            if domain_count.get(domain, 0) < 3:
                deduped.append(r)
                domain_count[domain] = domain_count.get(domain, 0) + 1

        logger.info(f"Search returned {len(deduped)} unique results (from {len(results)} raw)")
        return deduped[:max_results]


search_orchestrator = SearchOrchestrator()
