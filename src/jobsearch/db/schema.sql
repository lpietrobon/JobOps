CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  canonical_key TEXT UNIQUE NOT NULL,
  company TEXT, title TEXT, location TEXT, remote_type TEXT, seniority TEXT, employment_type TEXT,
  compensation_min INTEGER, compensation_max INTEGER, compensation_currency TEXT,
  apply_url TEXT, source TEXT, source_job_id TEXT, description TEXT,
  first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, is_active INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'new', fit_score REAL, priority TEXT, summary TEXT, concerns_json TEXT, tags_json TEXT,
  last_content_hash TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS job_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, fetched_at TEXT NOT NULL, content_hash TEXT NOT NULL, raw_path TEXT, raw_excerpt TEXT, FOREIGN KEY(job_id) REFERENCES jobs(id));
CREATE TABLE IF NOT EXISTS job_events (id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER NOT NULL, event_type TEXT NOT NULL, event_at TEXT NOT NULL, note TEXT, metadata_json TEXT, FOREIGN KEY(job_id) REFERENCES jobs(id));
CREATE TABLE IF NOT EXISTS source_runs (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, status TEXT NOT NULL, jobs_seen INTEGER DEFAULT 0, jobs_new INTEGER DEFAULT 0, jobs_changed INTEGER DEFAULT 0, error TEXT);
CREATE TABLE IF NOT EXISTS classification_tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT UNIQUE NOT NULL, job_id INTEGER NOT NULL, exported_at TEXT NOT NULL, imported_at TEXT, status TEXT NOT NULL DEFAULT 'exported', output_path TEXT, metadata_json TEXT, FOREIGN KEY(job_id) REFERENCES jobs(id));
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_events_job ON job_events(job_id);
