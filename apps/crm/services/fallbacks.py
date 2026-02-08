from dataclasses import dataclass
from typing import List
import requests
from django.utils import timezone
from apps.crm.models import LeadSourceProfile, LeadImportJob, LeadStaging
from apps.helpdesk.helpdesk_apps.admin_panel.models import SystemSettings


@dataclass
class FallbackResult:
    names: List[str]
    items: List[dict]
    error: str = ""


def _not_configured(name: str) -> FallbackResult:
    return FallbackResult(names=[], items=[], error=f"{name} not configured")


def _get_settings():
    return SystemSettings.get_settings()


def _build_query(profile: LeadSourceProfile) -> str:
    parts = [profile.keywords or ""]
    if getattr(profile, "ort", ""):
        parts.append(profile.ort)
    return " ".join([p for p in parts if p]).strip()


def _normalize_names(names: List[str], max_count: int) -> List[str]:
    seen = set()
    cleaned = []
    for name in names:
        if not name:
            continue
        value = str(name).strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(value)
        if len(cleaned) >= max_count:
            break
    return cleaned


def _serpapi_fetch(profile: LeadSourceProfile, max_count: int) -> FallbackResult:
    settings_obj = _get_settings()
    api_key = settings_obj.crm_serpapi_key
    if not api_key:
        return _not_configured("SerpAPI")
    query = _build_query(profile)
    if not query:
        return FallbackResult(names=[], items=[], error="SerpAPI query is empty.")
    try:
        limit = min(max_count, 100)
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": limit,
        }
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        names = []
        items = []
        for item in data.get("local_results", []) or []:
            title = item.get("title") or item.get("name")
            if title:
                names.append(title)
                items.append({"name": title, "url": item.get("website") or item.get("link")})
        for item in data.get("organic_results", []) or []:
            title = item.get("title")
            if title:
                names.append(title)
                items.append({"name": title, "url": item.get("link")})
        return FallbackResult(names=_normalize_names(names, max_count=limit), items=items)
    except Exception as exc:
        return FallbackResult(names=[], items=[], error=f"SerpAPI error: {exc}")


def _dataforseo_fetch(profile: LeadSourceProfile, max_count: int) -> FallbackResult:
    settings_obj = _get_settings()
    login = settings_obj.crm_dataforseo_login
    password = settings_obj.crm_dataforseo_password
    if not (login and password):
        return _not_configured("DataForSEO")
    query = _build_query(profile)
    if not query:
        return FallbackResult(names=[], items=[], error="DataForSEO query is empty.")
    location_name = profile.ort or "Germany"
    limit = min(max_count, 100)
    payload = [
        {
            "keyword": query,
            "location_name": location_name,
            "language_code": "de",
            "depth": limit,
        }
    ]
    try:
        response = requests.post(
            "https://api.dataforseo.com/v3/serp/google/organic/live/advanced",
            auth=(login, password),
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status_code") not in (20000, 20001):
            return FallbackResult(names=[], items=[], error=f"DataForSEO status: {data.get('status_message')}")
        tasks = data.get("tasks") or []
        if not tasks or not tasks[0].get("result"):
            return FallbackResult(names=[], items=[], error="DataForSEO returned no results.")
        result = tasks[0]["result"][0]
        items = result.get("items") or []
        names = []
        result_items = []
        for item in items:
            if item.get("type") and item.get("type") != "organic":
                continue
            title = item.get("title") or item.get("domain") or item.get("website_name")
            if title:
                names.append(title)
                result_items.append({"name": title, "url": item.get("url")})
        return FallbackResult(names=_normalize_names(names, max_count=limit), items=result_items)
    except Exception as exc:
        return FallbackResult(names=[], items=[], error=f"DataForSEO error: {exc}")


def _bing_fetch(profile: LeadSourceProfile, max_count: int) -> FallbackResult:
    settings_obj = _get_settings()
    api_key = settings_obj.crm_bing_api_key
    if not api_key:
        return _not_configured("Bing Search API")
    query = _build_query(profile)
    if not query:
        return FallbackResult(names=[], items=[], error="Bing query is empty.")
    try:
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        limit = min(max_count, 50)
        params = {
            "q": query,
            "mkt": "de-DE",
            "count": limit,
            "responseFilter": "Webpages",
        }
        response = requests.get(
            "https://api.bing.microsoft.com/v7.0/search",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        names = []
        items = []
        for item in data.get("webPages", {}).get("value", []) or []:
            title = item.get("name")
            if title:
                names.append(title)
                items.append({"name": title, "url": item.get("url")})
        return FallbackResult(names=_normalize_names(names, max_count=limit), items=items)
    except Exception as exc:
        return FallbackResult(names=[], items=[], error=f"Bing Search error: {exc}")


FALLBACK_PROVIDERS = {
    "serpapi": _serpapi_fetch,
    "dataforseo": _dataforseo_fetch,
    "bing": _bing_fetch,
}


def run_fallback_import(profile: LeadSourceProfile, max_count: int) -> LeadImportJob:
    settings_obj = _get_settings()
    provider_order = settings_obj.crm_fallback_provider_order or []
    if not provider_order:
        raise RuntimeError("No fallback providers configured.")

    job = LeadImportJob.objects.create(
        profile=profile,
        status="running",
        requested_count=max_count,
        started_at=timezone.now(),
    )
    imported = 0
    errors = []

    for key in provider_order:
        provider = FALLBACK_PROVIDERS.get(key)
        if not provider:
            errors.append(f"Unknown provider: {key}")
            continue
        result = provider(profile, max_count)
        if result.error:
            errors.append(result.error)
        result_items = result.items or [{"name": name} for name in result.names]
        if result_items:
            for item in result_items[:max_count]:
                company = item.get("name") or ""
                website = item.get("url") or ""
                raw_data = {"company_name": company, "fallback_provider": key}
                if website:
                    raw_data["website"] = website
                LeadStaging.objects.create(
                    profile=profile,
                    name="",
                    company=company,
                    email="",
                    phone="",
                    source="SearchFallback",
                    status="incomplete",
                    raw_data=raw_data,
                )
                imported += 1
            break

    job.status = "completed" if imported > 0 else "failed"
    job.imported_count = imported
    job.skipped_count = 0
    job.error_message = "; ".join([e for e in errors if e])[:500]
    job.finished_at = timezone.now()
    job.save(update_fields=["status", "imported_count", "skipped_count", "error_message", "finished_at"])
    return job
