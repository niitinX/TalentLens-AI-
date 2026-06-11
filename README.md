# TalentLens AI

TalentLens AI is a recruiter-style candidate ranking system for hackathon submissions. It reads a job description, analyzes candidate profiles, scores fit using a hybrid of semantic overlap, skill evidence, career relevance, and risk penalties, then exports a ranked shortlist.

## What this workspace is for

The project is designed around the shared hackathon brief:

- Rank candidates like a recruiter, not by keyword matching alone.
- Use the full profile: career history, skills, platform signals, and evidence.
- Produce a top-100 shortlist and a submission CSV.
- Keep ranking offline and CPU-only.

## Current MVP shape

- `rank.py` runs the scoring pipeline from the command line.
- `app.py` provides a Streamlit demo for uploading a job description and candidate dataset.
- `talentlens/` contains the ranking logic, data models, and file helpers.
- `scripts/run_baseline_check.py` runs the full dataset through the current scorer and validates the generated submission CSV.

## Reproduce

The ranking command now defaults to the bundled hackathon job description, so the submission can be generated with:

```bash
python rank.py --candidates ./India_runs_data_and_ai_challenge/candidates.jsonl --out ./submission.csv
```

## Next step

Run the full baseline on the official dataset, inspect the top-100 shortlist, and tune the role-specific penalties for keyword stuffing, research-only profiles, and weak behavioral signals.
