from __future__ import annotations

import tempfile
from pathlib import Path
import sys


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))
sys.path.insert(0, str(WORKSPACE_ROOT / "India_runs_data_and_ai_challenge"))

from talentlens.io import load_candidates, save_ranked_candidates_csv
from talentlens.scoring import rank_candidates
from validate_submission import validate_submission


def main() -> None:
    job_path = WORKSPACE_ROOT / "India_runs_data_and_ai_challenge" / "job_description.docx"
    candidates_path = WORKSPACE_ROOT / "India_runs_data_and_ai_challenge" / "candidates.jsonl"

    from talentlens.io import load_job_description

    print(f"loading job description: {job_path}")
    job_text = load_job_description(job_path)

    print(f"loading candidates: {candidates_path}")
    candidates = load_candidates(candidates_path)
    print(f"ranking {len(candidates)} candidates")
    ranked = rank_candidates(job_text, candidates, top_k=100)

    print(f"loaded={len(candidates)}")
    print(f"ranked={len(ranked)}")
    print("top5=")
    for item in ranked[:5]:
        print(f"  {item.candidate.candidate_id},{item.score:.4f},{' | '.join(item.reasons)}")

    with tempfile.TemporaryDirectory() as temp_dir:
        out_path = Path(temp_dir) / "submission.csv"
        print("writing submission csv")
        save_ranked_candidates_csv(ranked, out_path)
        print("validating submission csv")
        errors = validate_submission(out_path)
        print(f"validation_errors={len(errors)}")
        for error in errors[:5]:
            print(error)


if __name__ == "__main__":
    main()