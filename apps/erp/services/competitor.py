from decimal import Decimal
import re
import requests
from bs4 import BeautifulSoup
from django.core.cache import cache
from django.utils import timezone
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


class CompetitorPriceProvider:
    def fetch_price(self, product) -> Decimal | None:
        raise NotImplementedError


class GeizhalsProvider(CompetitorPriceProvider):
    def fetch_price(self, product) -> Decimal | None:
        if not _rate_limit_ok():
            return None
        query = _build_query(product)
        if not query:
            return None
        url = f"https://geizhals.de/?fs={requests.utils.quote(query)}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Referer": "https://geizhals.de/",
            "Connection": "keep-alive",
        }
        try:
            response = requests.get(url, headers=headers, timeout=25)
            response.raise_for_status()
            price, source = _extract_price_from_html(response.text)
            _store_last_debug(query, url, price, source, response.text)
            return price
        except Exception as exc:
            _store_last_debug(query, url, None, f"http_error:{exc}", "")
            return None


class ApiProvider(CompetitorPriceProvider):
    def __init__(self, url: str, api_key: str):
        self.url = url
        self.api_key = api_key

    def fetch_price(self, product) -> Decimal | None:
        if not self.url:
            return None
        params = {
            'q': product.name,
        }
        if product.sku:
            params['sku'] = product.sku
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        try:
            response = requests.get(self.url, params=params, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            value = data.get('price_net') or data.get('price')
        except Exception as exc:
            _store_last_debug(params.get('q', ''), self.url, None, f"api_error:{exc}", "")
            return None
        if value is None:
            return None
        try:
            price = Decimal(str(value))
            _store_last_debug(params.get('q', ''), self.url, price, 'api', str(data)[:8000])
            return price
        except Exception:
            return None


def _rate_limit_ok() -> bool:
    key = "erp_geizhals_requests_per_hour"
    count = cache.get(key, 0)
    if count >= 60:
        return False
    if count == 0:
        cache.set(key, 1, 3600)
    else:
        try:
            cache.incr(key)
        except Exception:
            cache.set(key, count + 1, 3600)
    return True


def _build_query(product) -> str:
    parts = [product.name]
    if product.sku:
        parts.append(product.sku)
    return " ".join([p for p in parts if p]).strip()


def _extract_price_from_html(html: str) -> tuple[Decimal | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    meta_price = soup.find("meta", {"itemprop": "price"})
    if meta_price and meta_price.get("content"):
        try:
            return Decimal(str(meta_price["content"]).replace(",", ".")), "meta[itemprop=price]"
        except Exception:
            pass

    candidates = []
    for node in soup.select('[data-qa*="price"], .price, .gh_price, .gh_price_entry'):
        value = node.get_text(" ", strip=True)
        if value:
            candidates.append(value)
    text = " ".join(candidates) if candidates else soup.get_text(" ", strip=True)
    prices = _extract_prices_from_text(text)
    if prices:
        return min(prices), "css/regex"
    return None, "not_found"


def _extract_prices_from_text(text: str) -> list[Decimal]:
    prices = []
    for match in re.findall(r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€", text):
        try:
            prices.append(Decimal(match.replace(".", "").replace(",", ".")))
        except Exception:
            continue
    for match in re.findall(r"€\s*(\d{1,3}(?:\.\d{3})*,\d{2})", text):
        try:
            prices.append(Decimal(match.replace(".", "").replace(",", ".")))
        except Exception:
            continue
    return prices


def _store_last_debug(query: str, url: str, price: Decimal | None, source: str, html: str):
    cache.set(
        "erp_geizhals_last_debug",
        {
            "query": query,
            "url": url,
            "price": str(price) if price is not None else "",
            "source": source,
            "at": timezone.now().isoformat(timespec="seconds"),
            "html_snippet": html[:8000],
        },
        3600,
    )


def get_provider():
    settings_obj = SystemSettings.get_settings()
    if not settings_obj.erp_competitor_scrape_enabled:
        return None
    if not settings_obj.erp_competitor_accept_terms:
        return None
    provider = (settings_obj.erp_competitor_provider or '').lower()
    if provider == 'geizhals':
        return GeizhalsProvider()
    if provider == 'api':
        return ApiProvider(settings_obj.erp_competitor_api_url, settings_obj.erp_competitor_api_key)
    return None
