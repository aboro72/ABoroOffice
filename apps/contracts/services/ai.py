import json
import os
import re
from typing import Tuple
from django.utils import timezone
from apps.core.services.bedrock import BedrockService

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    try:
        from PyPDF2 import PdfReader
    except Exception:
        PdfReader = None

try:
    import docx
except Exception:  # pragma: no cover
    docx = None


MAX_INPUT_CHARS = 20000


def _read_pdf(path: str) -> str:
    if not PdfReader:
        raise RuntimeError("PyPDF2 not installed")
    reader = PdfReader(path)
    text = []
    for page in reader.pages:
        try:
            text.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(text)


def _read_docx(path: str) -> str:
    if not docx:
        raise RuntimeError("python-docx not installed")
    document = docx.Document(path)
    return "\n".join([p.text for p in document.paragraphs if p.text])


def _extract_text(file_path: str | None, notes: str | None) -> str:
    parts = []
    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            parts.append(_read_pdf(file_path))
        elif ext in ('.docx', '.doc'):
            parts.append(_read_docx(file_path))
        else:
            # Unsupported file, ignore for now
            parts.append("")
    if notes:
        parts.append(notes)
    text = "\n".join([p for p in parts if p]).strip()
    if len(text) > MAX_INPUT_CHARS:
        text = text[:MAX_INPUT_CHARS]
    return text


def _extract_json(text: str) -> dict:
    if not text:
        return {}
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def analyze_contract(contract) -> Tuple[dict, str]:
    text = _extract_text(contract.file.path if contract.file else None, contract.notes)
    if not text:
        contract.ai_status = 'error'
        contract.ai_error = 'Kein Text aus Datei/Notizen gefunden.'
        contract.save(update_fields=['ai_status', 'ai_error'])
        return {}, "Kein Text aus Datei/Notizen gefunden."

    system = (
        "Du bist ein Assistent für Vertragsanalyse. "
        "Gib JSON zurück mit Schlüsseln: summary, risks, checklist, key_dates. "
        "summary: kurzer Absatz. risks: Liste von Punkten. "
        "checklist: Liste fehlender/unklarer Klauseln. "
        "key_dates: Liste von {label, date, note}. "
        "Antworte NUR mit JSON."
    )
    prompt = f"Analysiere diesen Vertragstext:\n{text}"
    service = BedrockService()
    contract.ai_status = 'running'
    contract.ai_error = ''
    contract.save(update_fields=['ai_status', 'ai_error'])
    try:
        response = service.converse(prompt, system=system)
    except Exception as exc:
        contract.ai_status = 'error'
        contract.ai_error = str(exc)
        contract.save(update_fields=['ai_status', 'ai_error'])
        return {}, str(exc)
    data = _extract_json(response)
    if not data:
        contract.ai_status = 'error'
        contract.ai_error = 'Konnte JSON aus KI-Antwort nicht lesen.'
        contract.save(update_fields=['ai_status', 'ai_error'])
        return {}, "Konnte JSON aus KI-Antwort nicht lesen."

    contract.ai_summary = data.get('summary', '')
    contract.ai_risks = data.get('risks', [])
    contract.ai_checklist = data.get('checklist', [])
    contract.ai_key_dates = data.get('key_dates', [])
    contract.ai_last_analyzed = timezone.now()
    contract.ai_status = 'done'
    contract.ai_error = ''
    contract.save(update_fields=['ai_summary', 'ai_risks', 'ai_checklist', 'ai_key_dates', 'ai_last_analyzed', 'ai_status', 'ai_error'])
    return data, ""
