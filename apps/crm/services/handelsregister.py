import re
import html
import requests
from datetime import timedelta
from pathlib import Path
from django.utils import timezone
from apps.crm.models import LeadSourceProfile, LeadImportJob, LeadStaging, SourceRequestLog


SOURCE_KEY = "handelsregister"
HANDELSREGISTER_SEARCH_URL = "https://www.handelsregister.de/rp_web/erweitertesuche/welcome.xhtml"
HANDELSREGISTER_ENDPOINTS = [
    "https://www.handelsregister.de/rp_web/erweitertesuche/welcome.xhtml",
    "https://www.handelsregister.de/rp_web/erweitertesuche.xhtml",
    "https://www.handelsregister.de/rp_web/mask.do?Typ=n",
    "https://www.handelsregister.de/rp_web/mask.do?Typ=e",
]

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except Exception:
    HAS_PLAYWRIGHT = False
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except Exception:
    HAS_BS4 = False
RATE_LIMIT_PER_HOUR = 60


class RateLimitError(RuntimeError):
    pass


def _check_rate_limit(required=1):
    window_start = timezone.now() - timedelta(hours=1)
    count = SourceRequestLog.objects.filter(
        source=SOURCE_KEY,
        requested_at__gte=window_start,
    ).count()
    if count + required > RATE_LIMIT_PER_HOUR:
        raise RateLimitError("Rate limit reached (60/h).")


def _log_request():
    SourceRequestLog.objects.create(source=SOURCE_KEY)


def _parse_results(html_text):
    results = []
    if HAS_BS4:
        soup = BeautifulSoup(html_text, "html.parser")
        tbody = soup.find("tbody", id="ergebnissForm:selectedSuchErgebnisFormTable_data")
        if not tbody:
            return results
        for row in tbody.find_all("tr", recursive=False):
            span = row.select_one("td.paddingBottom20Px span.marginLeft20")
            if not span:
                continue
            name = " ".join(span.get_text(strip=True).split())
            if name and len(name) > 2:
                results.append(name)
        return results

    # Fallback: regex extraction from result rows
    for match in re.findall(
        r'<td[^>]*class="[^"]*paddingBottom20Px[^"]*"[^>]*>\\s*<span[^>]*class="[^"]*marginLeft20[^"]*"[^>]*>(.*?)</span>',
        html_text,
        flags=re.S | re.I,
    ):
        name = re.sub(r"<[^>]+>", " ", match)
        name = re.sub(r"\s+", " ", name).strip()
        if name and len(name) > 2:
            results.append(name)
    # de-duplicate while preserving order
    seen = set()
    unique = []
    for item in results:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _extract_viewstate(html_text):
    match = re.search(r'name="javax\.faces\.ViewState"\s+value="([^"]+)"', html_text)
    if match:
        return match.group(1)
    return None


def _keyword_mode_value(mode):
    return {
        'all': '1',
        'min': '2',
        'exact': '3',
    }.get(mode, '1')


def _bool_true(value):
    return "true" if value else ""


def _build_search_payload(profile: LeadSourceProfile):
    keywords = " ".join([k.strip() for k in profile.keywords.split(",") if k.strip()])
    payload = {
        "neueSuche": "false",
        "schlagwoerter": keywords,
        "schlagwortOptionen": _keyword_mode_value(profile.keyword_mode),
        "schlagwortSuche": "",
        "gegenstand": "",
        "registerArt": profile.register_art or "alle",
        "registerNummer": profile.register_nummer or "",
        "registerGericht": profile.register_gericht or "",
        "rechtsform": profile.rechtsform or "",
        "postleitzahl": profile.postleitzahl or "",
        "strasse": profile.strasse or "",
        "ort": profile.ort or "",
        "niederlassung": profile.niederlassung or "",
        "suchTyp": profile.search_type or "n",
        "ergebnisseProSeite": str(profile.results_per_page),
        "suchOptionenAehnlich": _bool_true(profile.suchoptionen_aehnlich),
        "suchOptionenGeloescht": _bool_true(profile.suchoptionen_geloescht),
        "suchOptionenNurZNneuenRechts": _bool_true(profile.suchoptionen_nur_zn_neuen_rechts),
        "btnSuche": "Suchen",
    }
    # Bundesländer
    payload.update({
        "bundeslandBW": "on" if profile.bundesland_bw else "",
        "bundeslandBY": "on" if profile.bundesland_by else "",
        "bundeslandBE": "on" if profile.bundesland_be else "",
        "bundeslandBR": "on" if profile.bundesland_br else "",
        "bundeslandHB": "on" if profile.bundesland_hb else "",
        "bundeslandHH": "on" if profile.bundesland_hh else "",
        "bundeslandHE": "on" if profile.bundesland_he else "",
        "bundeslandMV": "on" if profile.bundesland_mv else "",
        "bundeslandNI": "on" if profile.bundesland_ni else "",
        "bundeslandNW": "on" if profile.bundesland_nw else "",
        "bundeslandRP": "on" if profile.bundesland_rp else "",
        "bundeslandSL": "on" if profile.bundesland_sl else "",
        "bundeslandSN": "on" if profile.bundesland_sn else "",
        "bundeslandST": "on" if profile.bundesland_st else "",
        "bundeslandSH": "on" if profile.bundesland_sh else "",
        "bundeslandTH": "on" if profile.bundesland_th else "",
    })
    return payload


def _extract_form(html_text, form_id):
    match = re.search(
        rf'<form[^>]*id="{re.escape(form_id)}"[^>]*>(.*?)</form>',
        html_text,
        flags=re.S | re.I,
    )
    if not match:
        return None, None
    form_block = match.group(0)
    inner = match.group(1)
    action_match = re.search(r'action="([^"]+)"', form_block, flags=re.I)
    action = action_match.group(1) if action_match else ""
    return inner, action


def _parse_form_fields(inner_html):
    fields = {}
    # inputs
    for match in re.finditer(r'<input[^>]*>', inner_html, flags=re.I):
        tag = match.group(0)
        name_match = re.search(r'name="([^"]+)"', tag, flags=re.I)
        if not name_match:
            continue
        name = name_match.group(1)
        value_match = re.search(r'value="([^"]*)"', tag, flags=re.I)
        value = value_match.group(1) if value_match else ""
        fields[name] = html.unescape(value)
    # textareas
    for match in re.finditer(r'<textarea[^>]*name="([^"]+)"[^>]*>(.*?)</textarea>', inner_html, flags=re.S | re.I):
        name = match.group(1)
        value = html.unescape(re.sub(r'<[^>]+>', '', match.group(2)))
        fields[name] = value
    # selects (take selected option if present, else first)
    for match in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', inner_html, flags=re.S | re.I):
        name = match.group(1)
        options = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>', match.group(2), flags=re.I)
        selected = re.search(r'<option[^>]*value="([^"]*)"[^>]*selected', match.group(2), flags=re.I)
        if selected:
            fields[name] = html.unescape(selected.group(1))
        elif options:
            fields[name] = html.unescape(options[0])
    return fields


def _http_fetch_html(profile: LeadSourceProfile):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })

    def _abs_url(path):
        if path.startswith("http"):
            return path
        if not path.startswith("/"):
            return f"https://www.handelsregister.de/{path}"
        return f"https://www.handelsregister.de{path}"

    # Initial GET
    resp = session.get(HANDELSREGISTER_SEARCH_URL, timeout=30)
    resp.raise_for_status()
    html_text = resp.text

    # Cookie acceptance is optional for the search form; skipping avoids session resets.

    # Extract search form
    form_inner, form_action = _extract_form(html_text, "form")
    if not form_inner:
        raise RuntimeError("Suche-Formular nicht gefunden.")

    form_fields = _parse_form_fields(form_inner)

    def _build_payloads(fields):
        keywords = " ".join([k.strip() for k in profile.keywords.split(",") if k.strip()])
        base_payload = {
            "form": "form",
            "javax.faces.ViewState": fields.get("javax.faces.ViewState", ""),
            "suchTyp": fields.get("suchTyp", "e"),
            "form:schlagwoerter": keywords,
            "form:schlagwortOptionen": _keyword_mode_value(profile.keyword_mode),
            "form:ergebnisseProSeite_input": str(profile.results_per_page),
            "form:btnSuche": "Suchen",
        }

        payload = dict(base_payload)
        if profile.register_art and profile.register_art != "alle":
            payload["form:registerArt_input"] = profile.register_art
        if profile.register_nummer:
            payload["form:registerNummer"] = profile.register_nummer
        if profile.register_gericht:
            payload["form:registergericht_input"] = profile.register_gericht
        if profile.rechtsform:
            payload["form:rechtsform_input"] = profile.rechtsform
        if profile.postleitzahl:
            payload["form:postleitzahl"] = profile.postleitzahl
        if profile.strasse:
            payload["form:strasse"] = profile.strasse
        if profile.ort:
            payload["form:ort"] = profile.ort
        if profile.niederlassung:
            payload["form:NiederlassungSitz"] = profile.niederlassung

        if profile.suchoptionen_aehnlich:
            payload["form:aenlichLautendeSchlagwoerterBoolChkbox_input"] = "on"
        if profile.suchoptionen_geloescht:
            payload["form:auchGeloeschte_input"] = "on"
        if profile.suchoptionen_nur_zn_neuen_rechts:
            payload["form:nurZweigniederlassungenBoolChkbox_input"] = "on"

        bundesland_map = {
            'bundesland_bw': 'Baden-Württemberg',
            'bundesland_by': 'Bayern',
            'bundesland_be': 'Berlin',
            'bundesland_br': 'Brandenburg',
            'bundesland_hb': 'Bremen',
            'bundesland_hh': 'Hamburg',
            'bundesland_he': 'Hessen',
            'bundesland_mv': 'Mecklenburg-Vorpommern',
            'bundesland_ni': 'Niedersachsen',
            'bundesland_nw': 'Nordrhein-Westfalen',
            'bundesland_rp': 'Rheinland-Pfalz',
            'bundesland_sl': 'Saarland',
            'bundesland_sn': 'Sachsen',
            'bundesland_st': 'Sachsen-Anhalt',
            'bundesland_sh': 'Schleswig-Holstein',
            'bundesland_th': 'Thüringen',
        }
        for field, label in bundesland_map.items():
            if getattr(profile, field):
                payload[f"form:{label}_input"] = "on"

        return base_payload, payload

    base_payload, form_fields = _build_payloads(form_fields)

    # Submit form
    action_url = _abs_url(form_action) if form_action else HANDELSREGISTER_SEARCH_URL
    for attempt in range(2):
        try:
            Path("logs").mkdir(exist_ok=True)
            Path("logs/handelsregister_payload.txt").write_text(
                "\n".join([f"{k}={v}" for k, v in form_fields.items()]),
                encoding="utf-8",
            )
        except Exception:
            pass
        resp = session.post(action_url, data=form_fields, timeout=30)
        resp.raise_for_status()
        html_text = resp.text
        try:
            Path("logs").mkdir(exist_ok=True)
            Path("logs/handelsregister_search.html").write_text(html_text, encoding="utf-8")
            Path("logs/handelsregister_after_submit.html").write_text(html_text, encoding="utf-8")
        except Exception:
            pass
        if ("Wählen Sie bitte mindestens einen Suchparameter aus" in html_text or
                "sucheErgebnisse" not in resp.url) and attempt == 0:
            resp = session.post(action_url, data=base_payload, timeout=30)
            resp.raise_for_status()
            html_text = resp.text
            try:
                Path("logs").mkdir(exist_ok=True)
                Path("logs/handelsregister_after_submit.html").write_text(html_text, encoding="utf-8")
            except Exception:
                pass
            if "Wählen Sie bitte mindestens einen Suchparameter aus" not in html_text:
                break
            resp = session.get(HANDELSREGISTER_SEARCH_URL, timeout=30)
            resp.raise_for_status()
            html_text = resp.text
            form_inner, form_action = _extract_form(html_text, "form")
            if form_inner:
                base_payload, form_fields = _build_payloads(_parse_form_fields(form_inner))
            continue
        break
    return html_text


def _playwright_fetch_html(profile: LeadSourceProfile):
    if not HAS_PLAYWRIGHT:
        raise RuntimeError("Playwright not available")
    keywords = " ".join([k.strip() for k in profile.keywords.split(",") if k.strip()])
    html = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="de-DE",
        )
        page = context.new_page()

        for attempt in range(2):
            page.goto(HANDELSREGISTER_SEARCH_URL, wait_until="domcontentloaded", timeout=30000)

            # Accept cookie banner if present
            if page.locator('a[id="cookieForm:j_idt17"]').count():
                page.click('a[id="cookieForm:j_idt17"]')
                page.wait_for_timeout(500)

            # Fallback: direct endpoint navigation if form not present
            if not page.locator('form#form').count():
                response = None
                for url in HANDELSREGISTER_ENDPOINTS:
                    response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    if response and response.status != 404:
                        break

            page.wait_for_selector('form#form', state="attached", timeout=30000)

            # Save search form HTML for debugging
            try:
                Path("logs").mkdir(exist_ok=True)
                Path("logs/handelsregister_before_submit.html").write_text(page.content(), encoding="utf-8")
            except Exception:
                pass

            # Fill inputs if present
            if keywords:
                if page.locator('textarea[name="form:schlagwoerter"]').count():
                    page.fill('textarea[name="form:schlagwoerter"]', keywords)
                elif page.locator('input[name="form:schlagwoerter"]').count():
                    page.fill('input[name="form:schlagwoerter"]', keywords)

            # Schlagwort-Optionen (radio)
            option_value = _keyword_mode_value(profile.keyword_mode)
            if page.locator(f'input[name="form:schlagwortOptionen"][value="{option_value}"]').count():
                page.check(f'input[name="form:schlagwortOptionen"][value="{option_value}"]')

            if page.locator('select[name="form:registerArt_input"]').count():
                page.select_option('select[name="form:registerArt_input"]', profile.register_art or "")
            if page.locator('input[name="form:registerNummer"]').count():
                page.fill('input[name="form:registerNummer"]', profile.register_nummer or "")
            if page.locator('input[name="form:registerGericht"]').count():
                page.fill('input[name="form:registerGericht"]', profile.register_gericht or "")
            if page.locator('input[name="form:rechtsform"]').count():
                page.fill('input[name="form:rechtsform"]', profile.rechtsform or "")
            if page.locator('input[name="form:postleitzahl"]').count():
                page.fill('input[name="form:postleitzahl"]', profile.postleitzahl or "")
            if page.locator('input[name="form:strasse"]').count():
                page.fill('input[name="form:strasse"]', profile.strasse or "")
            if page.locator('input[name="form:ort"]').count():
                page.fill('input[name="form:ort"]', profile.ort or "")
            if page.locator('input[name="form:niederlassung"]').count():
                page.fill('input[name="form:niederlassung"]', profile.niederlassung or "")
            if page.locator('select[name="form:ergebnisseProSeite_input"]').count():
                page.select_option('select[name="form:ergebnisseProSeite_input"]', str(profile.results_per_page))

            if profile.suchoptionen_aehnlich:
                if page.locator('input[id="form:aenlichLautendeSchlagwoerterBoolChkbox_input"]').count():
                    page.check('input[id="form:aenlichLautendeSchlagwoerterBoolChkbox_input"]')
            if profile.suchoptionen_geloescht:
                if page.locator('input[id="form:auchGeloeschte_input"]').count():
                    page.check('input[id="form:auchGeloeschte_input"]')
            if profile.suchoptionen_nur_zn_neuen_rechts:
                if page.locator('input[id="form:nurZweigniederlassungenBoolChkbox_input"]').count():
                    page.check('input[id="form:nurZweigniederlassungenBoolChkbox_input"]')

            bundesland_map = {
                'bundesland_bw': 'Baden-Württemberg',
                'bundesland_by': 'Bayern',
                'bundesland_be': 'Berlin',
                'bundesland_br': 'Brandenburg',
                'bundesland_hb': 'Bremen',
                'bundesland_hh': 'Hamburg',
                'bundesland_he': 'Hessen',
                'bundesland_mv': 'Mecklenburg-Vorpommern',
                'bundesland_ni': 'Niedersachsen',
                'bundesland_nw': 'Nordrhein-Westfalen',
                'bundesland_rp': 'Rheinland-Pfalz',
                'bundesland_sl': 'Saarland',
                'bundesland_sn': 'Sachsen',
                'bundesland_st': 'Sachsen-Anhalt',
                'bundesland_sh': 'Schleswig-Holstein',
                'bundesland_th': 'Th?ringen',
            }
            for field, label in bundesland_map.items():
                if getattr(profile, field):
                    selector = f'input[id="form:{label}_input"]'
                    if page.locator(selector).count():
                        page.check(selector)

            # Submit search
            if page.locator('button[id="form:btnSuche"]').count():
                page.click('button[id="form:btnSuche"]', force=True)
            elif page.locator('input[id="form:btnSuche"]').count():
                page.click('input[id="form:btnSuche"]', force=True)
            else:
                page.evaluate("document.getElementById('form').submit()")

            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            html = page.content()
            try:
                Path("logs").mkdir(exist_ok=True)
                Path("logs/handelsregister_search.html").write_text(html, encoding="utf-8")
                Path("logs/handelsregister_after_submit.html").write_text(html, encoding="utf-8")
            except Exception:
                pass

            if ("Sitzungshinweis" in html or "Abgelaufene Session" in html) and attempt == 0:
                continue
            break

        context.close()
        browser.close()
        return html

def import_profile(profile: LeadSourceProfile, max_count=200):
    job = LeadImportJob.objects.create(profile=profile, status='running', started_at=timezone.now())
    imported = 0
    skipped = 0
    try:
        _check_rate_limit()
        _check_rate_limit(required=1)
        _log_request()
        html = _http_fetch_html(profile)
        if not html and HAS_PLAYWRIGHT:
            html = _playwright_fetch_html(profile)
        company_names = _parse_results(html)
        if not company_names:
            try:
                Path("logs").mkdir(exist_ok=True)
                Path("logs/handelsregister_last.html").write_text(html, encoding="utf-8")
            except Exception:
                pass
            # Save small hint for debugging
            job.status = 'completed'
            job.imported_count = 0
            job.skipped_count = 0
            job.requested_count = max_count
            job.error_message = "Keine Treffer geparst. HTML in logs/handelsregister_last.html."
            job.finished_at = timezone.now()
            job.save(update_fields=['status', 'imported_count', 'skipped_count', 'requested_count', 'error_message', 'finished_at'])
            return job

        for name in company_names[:max_count]:
            LeadStaging.objects.create(
                profile=profile,
                name="",
                company=name,
                email="",
                phone="",
                source="Handelsregister",
                status="incomplete",
                raw_data={"company_name": name},
            )
            imported += 1

        job.status = 'completed'
        job.imported_count = imported
        job.skipped_count = skipped
        job.requested_count = max_count
        job.finished_at = timezone.now()
        job.save(update_fields=['status', 'imported_count', 'skipped_count', 'requested_count', 'finished_at'])
        profile.last_run_at = timezone.now()
        profile.save(update_fields=['last_run_at'])
        return job
    except RateLimitError as exc:
        job.status = 'rate_limited'
        job.error_message = str(exc)
    except Exception as exc:
        job.status = 'failed'
        job.error_message = str(exc)
    job.finished_at = timezone.now()
    job.save(update_fields=['status', 'error_message', 'finished_at'])
    return job
