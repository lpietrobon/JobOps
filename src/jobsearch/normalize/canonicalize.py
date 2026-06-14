from __future__ import annotations
import hashlib, re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from jobsearch.models import NormalizedJob, RawJob

COMPANY_SUFFIXES = re.compile(r"\b(inc|inc\.|llc|ltd|corp|corporation|co\.|company)\b", re.I)
SPACE = re.compile(r"\s+")

def compact(text: str | None) -> str:
    return SPACE.sub(" ", (text or "").strip())

def canonical_company(company: str | None) -> str:
    return compact(COMPANY_SUFFIXES.sub("", company or "")).lower().strip(" ,.-")

def canonical_title(title: str | None) -> str:
    return compact((title or "").replace("/", " ")).lower()

def canonical_location(location: str | None) -> str:
    text = compact(location).lower()
    return text.replace("san francisco, ca", "san francisco").replace("sf bay area", "bay area")

def canonical_url(url: str | None) -> str:
    if not url: return ""
    s = urlsplit(url.strip())
    query = urlencode([(k,v) for k,v in parse_qsl(s.query) if not k.lower().startswith(("utm_", "gh_src"))])
    path = s.path.rstrip("/")
    return urlunsplit((s.scheme.lower(), s.netloc.lower(), path, query, ""))

def infer_remote(location: str | None, description: str | None = None) -> str | None:
    text = f"{location or ''} {description or ''}".lower()
    if "remote" in text: return "remote"
    if "hybrid" in text: return "hybrid"
    if "onsite" in text or "on-site" in text: return "onsite"
    return None

def infer_seniority(title: str | None) -> str | None:
    t = (title or "").lower()
    for key in ["principal", "staff", "senior", "lead", "manager", "junior", "intern"]:
        if key in t: return key
    return None

def normalize_raw_job(raw: RawJob) -> NormalizedJob:
    return NormalizedJob(compact(raw.company), compact(raw.title), compact(raw.location) or None,
        infer_remote(raw.location, raw.description), infer_seniority(raw.title), None, None, None, None,
        canonical_url(raw.apply_url) or raw.apply_url, raw.source, raw.source_job_id, raw.description, raw.raw)

def content_hash(job: NormalizedJob) -> str:
    parts = [job.title, job.company, job.location or "", str(job.compensation_min), str(job.compensation_max), job.description or "", job.apply_url]
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()

def canonical_key(job: NormalizedJob) -> str:
    identity = job.source_job_id or canonical_url(job.apply_url)
    text = "|".join([canonical_company(job.company), canonical_title(job.title), canonical_location(job.location), identity])
    return hashlib.sha256(text.encode()).hexdigest()
