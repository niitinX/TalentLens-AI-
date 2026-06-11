from __future__ import annotations

import argparse
from pathlib import Path

from talentlens.io import load_candidates, load_job_description, save_ranked_candidates_csv
from talentlens.role_profile import DEFAULT_JOB_DESCRIPTION_PATHS
from talentlens.scoring import rank_candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rank candidates for the TalentLens AI hackathon.")
    parser.add_argument("--job-description", help="Path to the job description file (.txt, .md, or .docx). Defaults to the bundled challenge JD.")
    parser.add_argument("--candidates", required=True, help="Path to the candidate dataset (.jsonl, .json, or .csv).")
    parser.add_argument("--output", "--out", dest="output", default="outputs/ranked_candidates.csv", help="Where to write the ranked CSV.")
    parser.add_argument("--top-k", type=int, default=100, help="Number of candidates to keep in the shortlist.")
    return parser


def _resolve_job_description_path(explicit_path: str | None) -> Path:
    if explicit_path:
        return Path(explicit_path)

    for candidate_path in DEFAULT_JOB_DESCRIPTION_PATHS:
        if candidate_path.exists():
            return candidate_path

    raise FileNotFoundError(
        "Job description file not found. Provide --job-description or place the bundled job_description.docx in the repo root or challenge folder."
    )


def main() -> None:
    args = build_parser().parse_args()
    job_text = load_job_description(_resolve_job_description_path(args.job_description))
    candidates = load_candidates(Path(args.candidates))
    ranked = rank_candidates(job_text, candidates, top_k=args.top_k)
    save_ranked_candidates_csv(ranked, Path(args.output))
    print(f"Ranked {len(ranked)} candidates -> {args.output}")


if __name__ == "__main__":
    main()
