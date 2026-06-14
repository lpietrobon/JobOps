from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

STATUSES = {"new","reviewed","saved","discarded","applied","recruiter_reply","interviewing","take_home","onsite","offer","rejected","closed"}
PRIORITIES = {"high","medium","low"}

@dataclass
class RawJob:
    company: str
    title: str
    apply_url: str
    source: str
    source_job_id: str | None = None
    location: str | None = None
    description: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

@dataclass
class NormalizedJob:
    company: str
    title: str
    location: str | None
    remote_type: str | None
    seniority: str | None
    employment_type: str | None
    compensation_min: int | None
    compensation_max: int | None
    compensation_currency: str | None
    apply_url: str
    source: str
    source_job_id: str | None
    description: str | None
    raw: dict[str, Any]
