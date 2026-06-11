from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from .models import Candidate, RankedCandidate
from .role_profile import NEGATIVE_TITLES, POSITIVE_CAREER_TERMS, PRODUCT_TERMS, RESEARCH_ONLY_TERMS


TITLE_POSITIVE_TERMS = {
    "machine learning engineer",
    "ml engineer",
    "applied scientist",
    "recommendation",
    "recommender",
    "search engineer",
    "retrieval",
    "ranking",
    "nlp engineer",
    "data scientist",
    "ai engineer",
    "llm",
}

TITLE_NEGATIVE_TERMS = {
    "hr",
    "human resources",
    "content writer",
    "marketing",
    "sales",
    "talent acquisition",
    "recruiter",
    "operations manager",
}

CAREER_POSITIVE_TERMS = {
    "machine learning",
    "ml",
    "llm",
    "retrieval",
    "ranking",
    "search",
    "recommendation",
    "embedding",
    "nlp",
    "information retrieval",
    "recommender",
    "vector",
    "semantic search",
    "python",
    "tensorflow",
    "pytorch",
    "spark",
    "airflow",
    "feature store",
}

CAREER_NEGATIVE_TERMS = {
    "content writer",
    "marketing",
    "sales",
    "hr",
    "recruiter",
    "customer support",
    "accounting",
    "civil engineer",
    "mechanical engineer",
    "operations manager",
    "project manager",
    "graphic designer",
}

STRONG_SIGNAL_KEYS = {
    "open_to_work",
    "github",
    "linkedin",
    "recent_activity",
    "last_active_days",
    "notice_period_days",
}

STOPWORDS = {
    "and",
    "or",
    "the",
    "a",
    "an",
    "of",
    "to",
    "for",
    "with",
    "in",
    "on",
    "by",
    "from",
    "as",
    "is",
    "are",
    "be",
    "this",
    "that",
    "we",
    "you",
    "they",
    "our",
    "their",
    "at",
    "it",
    "will",
}


@dataclass(slots=True)
class JobProfile:
    keywords: set[str]
    title_terms: set[str]
    seniority_terms: set[str]
    role_terms: set[str]


TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#-]{1,}")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def tokenize(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
    return [token for token in tokens if token not in STOPWORDS]


def build_candidate_text(candidate: Candidate) -> str:
    career_parts = []
    for entry in candidate.career_history[:2]:
        if not isinstance(entry, dict):
            continue
        career_parts.append(" ".join(str(entry.get(field, "")) for field in ("title", "company", "industry", "description")))

    signal_fields = (
        "open_to_work_flag",
        "profile_completeness_score",
        "recruiter_response_rate",
        "avg_response_time_hours",
        "github_activity_score",
        "last_active_date",
        "notice_period_days",
        "linkedin_connected",
    )
    signal_text = " ".join(f"{key} {candidate.signals.get(key, '')}" for key in signal_fields if candidate.signals.get(key, "") not in (None, "", []))
    skill_text = " ".join(candidate.skills[:12])
    parts = [
        candidate.name,
        candidate.headline,
        candidate.current_title,
        candidate.current_company,
        candidate.current_industry,
        candidate.location,
        candidate.country,
        candidate.summary,
        candidate.career_history_text[:1200],
        " ".join(career_parts),
        skill_text,
        signal_text,
    ]
    return normalize_text(" ".join(part for part in parts if part))


def infer_job_profile(job_text: str) -> JobProfile:
    normalized = normalize_text(job_text)
    tokens = set(tokenize(job_text))
    keywords = {token for token in tokens if len(token) > 3}
    title_terms = {term for term in TITLE_POSITIVE_TERMS if term in normalized}
    seniority_terms = {term for term in {"senior", "lead", "staff", "principal", "experienced", "years"} if term in normalized}
    role_terms = {term for term in POSITIVE_CAREER_TERMS if term in normalized}
    return JobProfile(keywords=keywords, title_terms=title_terms, seniority_terms=seniority_terms, role_terms=role_terms)


def _overlap_ratio(needle: Iterable[str], haystack: Iterable[str]) -> float:
    needle_set = {token.lower() for token in needle if token}
    haystack_set = {token.lower() for token in haystack if token}
    if not needle_set:
        return 0.0
    return len(needle_set & haystack_set) / len(needle_set)


def _title_score(title: str) -> float:
    normalized = normalize_text(title)
    if not normalized:
        return 0.0

    positive_hits = sum(1 for term in TITLE_POSITIVE_TERMS if term in normalized)
    negative_hits = sum(1 for term in TITLE_NEGATIVE_TERMS | NEGATIVE_TITLES if term in normalized)
    return max(0.0, min(1.0, 0.25 * positive_hits - 0.25 * negative_hits + 0.5))


def _career_evidence_score(candidate: Candidate, job_profile: JobProfile) -> float:
    history_text = normalize_text(candidate.career_history_text)
    if not history_text and candidate.career_history:
        history_text = normalize_text(" ".join(str(entry) for entry in candidate.career_history))

    positive_hits = sum(1 for term in POSITIVE_CAREER_TERMS if term in history_text)
    negative_hits = sum(1 for term in CAREER_NEGATIVE_TERMS if term in history_text)

    role_term_hits = sum(1 for term in job_profile.role_terms if term in history_text)
    title_term_hits = sum(1 for term in job_profile.title_terms if term in normalize_text(candidate.current_title))

    score = 0.1 * positive_hits + 0.15 * role_term_hits + 0.1 * title_term_hits - 0.12 * negative_hits
    if any(term in history_text for term in PRODUCT_TERMS | {"built", "owned", "designed"}):
        score += 0.1
    if any(term in history_text for term in {"services", "outsourcing", "staff augmentation", "agency"}):
        score -= 0.08
    if any(term in history_text for term in RESEARCH_ONLY_TERMS) and not any(term in history_text for term in PRODUCT_TERMS):
        score -= 0.15
    return max(0.0, min(1.0, score + 0.25))


def _skill_trust_score(candidate: Candidate, job_profile: JobProfile) -> float:
    if not candidate.skill_details:
        return 0.0

    relevant_skill_names = set()
    if job_profile.keywords:
        for detail in candidate.skill_details:
            name = str(detail.get("name", "")).strip().lower()
            if not name:
                continue
            if any(term in name for term in job_profile.keywords):
                relevant_skill_names.add(name)

    details_score = 0.0
    assessment_map = {str(key).lower(): value for key, value in candidate.signals.get("skill_assessment_scores", {}).items() if isinstance(value, (int, float))}

    for detail in candidate.skill_details:
        name = str(detail.get("name", "")).strip().lower()
        if not name:
            continue
        proficiency = str(detail.get("proficiency", "")).lower()
        endorsements = float(detail.get("endorsements", 0) or 0)
        duration_months = float(detail.get("duration_months", 0) or 0)
        assessment = float(assessment_map.get(name, -1))

        proficiency_weight = {
            "beginner": 0.15,
            "intermediate": 0.45,
            "advanced": 0.75,
            "expert": 1.0,
        }.get(proficiency, 0.2)
        endorsement_weight = min(1.0, math.log1p(max(0.0, endorsements)) / 4.0)
        duration_weight = min(1.0, duration_months / 36.0)
        assessment_weight = (assessment / 100.0) if assessment >= 0 else 0.0

        trust = 0.35 * proficiency_weight + 0.25 * endorsement_weight + 0.2 * duration_weight + 0.2 * assessment_weight
        if relevant_skill_names and name in relevant_skill_names:
            trust += 0.05
        details_score += min(1.0, trust)

    return max(0.0, min(1.0, details_score / max(1, len(candidate.skill_details))))


def _experience_score(years: float, target_low: float = 3.0, target_high: float = 12.0) -> float:
    if years <= 0:
        return 0.0
    if target_low <= years <= target_high:
        return 1.0
    if years < target_low:
        return max(0.0, years / target_low)
    return max(0.2, 1.0 - min(0.5, (years - target_high) / 20.0))


def _signal_score(candidate: Candidate) -> float:
    score = 0.0
    signals = {str(key).lower(): value for key, value in candidate.signals.items()}

    if str(signals.get("open_to_work", "")).lower() in {"true", "yes", "1"}:
        score += 0.3
    if str(signals.get("open_to_work_flag", "")).lower() in {"true", "yes", "1"}:
        score += 0.2

    github_value = signals.get("github") or signals.get("github_activity")
    if github_value:
        score += 0.2
    github_score = signals.get("github_activity_score")
    if isinstance(github_score, (int, float)) and github_score >= 0:
        score += min(0.25, float(github_score) / 400.0)

    linkedin_value = signals.get("linkedin")
    if linkedin_value:
        score += 0.1
    if str(signals.get("linkedin_connected", "")).lower() in {"true", "yes", "1"}:
        score += 0.1

    completeness = signals.get("profile_completeness_score")
    if isinstance(completeness, (int, float)):
        score += min(0.15, float(completeness) / 700.0)

    last_active = signals.get("last_active_days")
    if isinstance(last_active, (int, float)):
        score += max(0.0, 0.2 - min(0.2, float(last_active) / 365.0))
    last_active_date = signals.get("last_active_date")
    if isinstance(last_active_date, str) and last_active_date:
        score += 0.03

    notice_period = signals.get("notice_period_days")
    if isinstance(notice_period, (int, float)) and float(notice_period) <= 30:
        score += 0.2
    elif isinstance(notice_period, (int, float)) and float(notice_period) <= 90:
        score += 0.08

    response_rate = signals.get("recruiter_response_rate")
    if isinstance(response_rate, (int, float)):
        score += min(0.18, float(response_rate) * 0.18)

    interview_completion_rate = signals.get("interview_completion_rate")
    if isinstance(interview_completion_rate, (int, float)):
        score += min(0.12, float(interview_completion_rate) * 0.12)

    if str(signals.get("verified_email", "")).lower() in {"true", "yes", "1"}:
        score += 0.04
    if str(signals.get("verified_phone", "")).lower() in {"true", "yes", "1"}:
        score += 0.04

    return max(0.0, min(1.0, score))


def _risk_flags(candidate: Candidate, job_text: str) -> list[str]:
    flags: list[str] = []
    normalized_title = normalize_text(candidate.current_title)
    normalized_job = normalize_text(job_text)
    history_text = normalize_text(candidate.career_history_text)

    if any(term in normalized_title for term in TITLE_NEGATIVE_TERMS) and any(term in normalized_job for term in TITLE_POSITIVE_TERMS):
        flags.append("title_mismatch")

    if any(term in history_text for term in RESEARCH_ONLY_TERMS) and not any(term in history_text for term in PRODUCT_TERMS):
        flags.append("research_only")

    if candidate.experience_years and candidate.experience_years > 20:
        flags.append("very_high_experience")

    if len({skill.lower() for skill in candidate.skills}) < 3:
        flags.append("thin_skill_profile")

    if not candidate.signals:
        flags.append("missing_behavioral_signals")

    if len(candidate.skill_details) >= 12 and all(float(detail.get("endorsements", 0) or 0) <= 1 for detail in candidate.skill_details):
        flags.append("weak_skill_endorsements")

    if any(term in normalized_title for term in TITLE_NEGATIVE_TERMS | NEGATIVE_TITLES) and any(term in history_text for term in POSITIVE_CAREER_TERMS):
        flags.append("keyword_stuffing_risk")

    if str(candidate.signals.get("github_activity_score", -1)) == "-1":
        flags.append("no_github_linked")

    return flags


def rank_candidates(job_text: str, candidates: list[Candidate], top_k: int | None = None) -> list[RankedCandidate]:
    if not candidates:
        return []

    job_profile = infer_job_profile(job_text)
    job_tokens = tokenize(job_text)

    ranked: list[RankedCandidate] = []
    for candidate in candidates:
        candidate_tokens = tokenize(build_candidate_text(candidate))
        similarity = _overlap_ratio(job_profile.keywords, candidate_tokens)
        skill_overlap = _overlap_ratio(job_profile.keywords, tokenize(" ".join(candidate.skills + [candidate.summary, candidate.career_history_text, candidate.headline, candidate.current_title])))
        title_score = _title_score(candidate.current_title)
        experience_score = _experience_score(candidate.experience_years)
        career_evidence_score = _career_evidence_score(candidate, job_profile)
        skill_trust_score = _skill_trust_score(candidate, job_profile)
        signal_score = _signal_score(candidate)
        risk_flags = _risk_flags(candidate, job_text)
        risk_penalty = min(0.4, 0.07 * len(risk_flags))

        score = (
            0.28 * float(similarity)
            + 0.16 * skill_overlap
            + 0.16 * title_score
            + 0.14 * career_evidence_score
            + 0.12 * skill_trust_score
            + 0.10 * experience_score
            + 0.04 * signal_score
            - risk_penalty
        )
        score = max(0.0, min(1.0, score))

        reasons = []
        if skill_overlap >= 0.25:
            reasons.append("strong skill alignment")
        if float(similarity) >= 0.15:
            reasons.append("good semantic fit")
        if title_score >= 0.6:
            reasons.append("relevant role trajectory")
        if career_evidence_score >= 0.35:
            reasons.append("career evidence matches the role")
        if skill_trust_score >= 0.35:
            reasons.append("skills look credible")
        if signal_score >= 0.3:
            reasons.append("positive activity signals")
        if not reasons:
            reasons.append("baseline profile match")

        breakdown = {
            "semantic_fit": float(similarity),
            "skill_overlap": skill_overlap,
            "title_score": title_score,
            "career_evidence_score": career_evidence_score,
            "skill_trust_score": skill_trust_score,
            "experience_score": experience_score,
            "signal_score": signal_score,
            "risk_penalty": risk_penalty,
        }

        ranked.append(
            RankedCandidate(
                candidate=candidate,
                score=score,
                breakdown=breakdown,
                reasons=reasons,
                flags=risk_flags,
            )
        )

    ranked.sort(key=lambda item: (-round(item.score, 4), item.candidate.candidate_id))
    if top_k is not None:
        ranked = ranked[:top_k]
    return ranked
