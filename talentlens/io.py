from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable

from docx import Document

from .models import Candidate, RankedCandidate


def load_candidates(path: str | Path) -> list[Candidate]:
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix == ".jsonl":
        candidates: list[Candidate] = []
        with source.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                payload = json.loads(line)
                if isinstance(payload, dict):
                    candidates.append(Candidate.from_dict(payload))
        return candidates

    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        items = payload if isinstance(payload, list) else payload.get("candidates", [])
        return [Candidate.from_dict(item) for item in items if isinstance(item, dict)]

    if suffix == ".csv":
        candidates = []
        with source.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                candidates.append(Candidate.from_dict(dict(row)))
        return candidates

    raise ValueError(f"Unsupported candidate file format: {source.suffix}")


def load_job_description(path: str | Path) -> str:
    source = Path(path)
    suffix = source.suffix.lower()

    if suffix in {".txt", ".md"}:
        return source.read_text(encoding="utf-8")
    if suffix == ".docx":
        document = Document(str(source))
        return "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text.strip())

    raise ValueError(f"Unsupported job description format: {source.suffix}")


def save_ranked_candidates_csv(rows: Iterable[RankedCandidate], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for index, row in enumerate(rows, start=1):
            reasoning_parts = ["; ".join(row.reasons)] if row.reasons else []
            if row.flags:
                reasoning_parts.append(f"flags: {'; '.join(row.flags)}")
            writer.writerow([
                row.candidate.candidate_id,
                index,
                f"{row.score:.4f}",
                " | ".join(reasoning_parts),
            ])
