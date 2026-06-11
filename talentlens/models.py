from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Candidate:
    candidate_id: str
    name: str = ""
    headline: str = ""
    current_title: str = ""
    current_company: str = ""
    current_company_size: str = ""
    current_industry: str = ""
    location: str = ""
    country: str = ""
    experience_years: float = 0.0
    skills: list[str] = field(default_factory=list)
    skill_details: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    career_history_text: str = ""
    career_history: list[dict[str, Any]] = field(default_factory=list)
    education: list[dict[str, Any]] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Candidate":
        profile = payload.get("profile") if isinstance(payload.get("profile"), dict) else {}
        career_history = payload.get("career_history") if isinstance(payload.get("career_history"), list) else []
        education = payload.get("education") if isinstance(payload.get("education"), list) else []
        redrob_signals = payload.get("redrob_signals") if isinstance(payload.get("redrob_signals"), dict) else {}

        def get_first(keys: list[str], default: Any = "") -> Any:
            sources = (profile, payload)
            for key in keys:
                for source in sources:
                    value = source.get(key)
                    if value not in (None, "", []):
                        return value
            return default

        def coerce_skills(value: Any) -> list[str]:
            if isinstance(value, list) and value and isinstance(value[0], dict):
                return [str(item.get("name", "")).strip() for item in value if str(item.get("name", "")).strip()]
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str):
                return [item.strip() for item in value.split(",") if item.strip()]
            return []

        def coerce_skill_details(value: Any) -> list[dict[str, Any]]:
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            return []

        def coerce_float(value: Any) -> float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        candidate_id = str(get_first(["candidate_id", "id", "profile_id"], "")).strip()
        career_history_text = " ".join(
            " ".join(
                str(entry.get(field, ""))
                for field in ("title", "company", "industry", "description")
            )
            for entry in career_history
            if isinstance(entry, dict)
        ).strip()

        return cls(
            candidate_id=candidate_id,
            name=str(get_first(["anonymized_name", "name", "full_name", "candidate_name"], "")).strip(),
            headline=str(get_first(["headline"], "")).strip(),
            current_title=str(get_first(["current_title", "title", "headline", "role"], "")).strip(),
            current_company=str(get_first(["current_company"], "")).strip(),
            current_company_size=str(get_first(["current_company_size"], "")).strip(),
            current_industry=str(get_first(["current_industry"], "")).strip(),
            location=str(get_first(["location", "city", "country"], "")).strip(),
            country=str(get_first(["country"], "")).strip(),
            experience_years=coerce_float(get_first(["experience_years", "years_experience", "total_experience_years"], 0.0)),
            skills=coerce_skills(get_first(["skills", "skillset", "technical_skills"], [])),
            skill_details=coerce_skill_details(payload.get("skills") if "skills" in payload else profile.get("skills")),
            summary=str(get_first(["summary", "bio", "about", "profile_summary"], "")).strip(),
            career_history_text=career_history_text or str(get_first(["career_history_text", "experience", "experience_text", "work_history"], "")).strip(),
            career_history=[entry for entry in career_history if isinstance(entry, dict)],
            education=[entry for entry in education if isinstance(entry, dict)],
            signals=dict(redrob_signals or get_first(["signals", "platform_signals", "behavioral_signals"], {}) or {}),
            raw=payload,
        )


@dataclass(slots=True)
class RankedCandidate:
    candidate: Candidate
    score: float
    breakdown: dict[str, float]
    reasons: list[str]
    flags: list[str]
