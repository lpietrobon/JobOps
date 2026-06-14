# JobOps Local Job Search Pipeline

A lightweight, local-first CLI pipeline for discovering job postings, normalizing and deduplicating them, preserving user judgments in SQLite, exporting provider-agnostic classification tasks, importing structured results, and generating static reports.

## Quickstart

```bash
git clone <repo>
cd jobsearch-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp config.example.yaml config.yaml
jobctl init-db
jobctl ingest
jobctl export-classification-tasks --limit 20 --out data/tasks/pending_classification.jsonl
```

## Workflow

```text
ingest -> normalize -> dedupe -> persist -> export tasks -> external classification -> import results -> review/report
```

Discovery is recurring; judgment is persistent. Rediscovered jobs update `last_seen_at` and content snapshots without overwriting statuses such as `discarded`, `saved`, `applied`, or `rejected`.

## Data privacy

Local private files are ignored by Git: `config.yaml`, SQLite databases, raw/cache data, JSONL task files, generated reports, logs, credentials, tokens, private notes, and virtual environments. Do not commit credentials or real user data.

## Configuration

Copy `config.example.yaml` to `config.yaml` and edit source companies. v1 supports simple public API fetching for Greenhouse, Lever, Ashby, and custom public URLs. Browser automation and provider-specific LLM integrations are intentionally out of scope.

## Common commands

```bash
jobctl init-db
jobctl migrate
jobctl config-check
jobctl ingest
jobctl ingest --source greenhouse
jobctl export-classification-tasks --limit 50 --out data/tasks/pending_classification.jsonl
jobctl import-classifications data/tasks/classification_results.jsonl
jobctl latest --limit 20
jobctl latest --json
jobctl top --json
jobctl show <job_id> --json
jobctl saved
jobctl applied
jobctl discarded
jobctl stats --since 30d --json
jobctl source-health --json
jobctl save <job_id>
jobctl discard <job_id> --reason "wrong location"
jobctl applied <job_id>
jobctl reject <job_id> --reason "company rejection"
jobctl status <job_id> reviewed
jobctl note <job_id> "note text"
jobctl report
jobctl report --format md
jobctl report --format html
```

Every judgment command writes an append-only `job_events` row.

## Classification task JSONL schema

Each exported line is self-contained:

```json
{"task_id":"classify_job_20260613_000123","job_id":123,"company":"ExampleAI","title":"Staff ML Engineer","location":"San Francisco / Remote","source":"greenhouse","apply_url":"https://example.com/job/123","description":"trimmed job description","known_fields":{"seniority":"staff","compensation_min":null,"compensation_max":null,"remote_type":"hybrid"},"user_preferences":{"target_roles":["machine learning"],"negative_keywords":["crypto"],"accepted_locations":["Remote"]},"required_output_schema":{"task_id":"string","job_id":"integer","fit_score":"integer 0-100","priority":"high|medium|low","summary":"string","concerns":["string"],"tags":["string"],"suggested_status":"new|reviewed|saved|discarded|null"}}
```

## Classification result JSONL schema

External tools should write one JSON object per line:

```json
{"task_id":"classify_job_20260613_000123","job_id":123,"fit_score":88,"priority":"high","summary":"Strong fit for ML and integrity work.","concerns":["Compensation not listed"],"tags":["ml","integrity"],"suggested_status":"reviewed"}
```

The importer validates `task_id`, `job_id`, score range, priority enum, list fields, and suggested status. Bad rows are reported and skipped; valid rows are imported.

## OpenClaw instructions

OpenClaw or any assistant should interact only through `jobctl` and JSONL contracts:

1. Read this README.
2. Run `jobctl latest --json`.
3. Run `jobctl export-classification-tasks --limit 50 --out data/tasks/pending_classification.jsonl`.
4. Read the pending classification file.
5. Produce `data/tasks/classification_results.jsonl` using the documented schema.
6. Run `jobctl import-classifications data/tasks/classification_results.jsonl`.
7. Run `jobctl report`.
8. Summarize best opportunities and next actions.

OpenClaw must not edit SQLite directly, read credentials or browser profiles, send email, apply to jobs, or alter statuses without user confirmation.

## Reports

`jobctl report` writes static `reports/latest.md` and `reports/latest.html` with high/medium priority jobs, awaiting classification, handled jobs with changes, saved/applied follow-up, source health, and recent events. Reports are valid even when the database is empty.

## Troubleshooting

- **Database not initialized**: run `jobctl init-db`.
- **No jobs found**: verify `config.yaml` source companies and network access; run `jobctl source-health --json`.
- **Duplicate jobs**: check source job IDs and canonical apply URLs; conservative soft duplicates are not silently merged.
- **Malformed classification result**: inspect importer error output and ensure JSONL rows match the result schema.
- **Source fetch failed**: source errors are recorded in `source_runs`; other sources continue.
- **Report empty**: run `jobctl ingest`, then export/import classifications, or confirm jobs exist with `jobctl latest --json`.
