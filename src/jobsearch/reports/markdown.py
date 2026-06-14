from jobsearch.db.repository import Repository

def generate_markdown(db_path="data/jobs.sqlite"):
    repo=Repository(db_path)
    sections=[("New high-priority jobs", "priority='high' AND status IN ('new','reviewed')"),("New medium-priority jobs", "priority='medium' AND status IN ('new','reviewed')"),("Jobs awaiting classification", "fit_score IS NULL AND status='new'"),("Previously handled jobs with meaningful changes", "status NOT IN ('new','reviewed')"),("Saved jobs needing action", "status='saved'"),("Applied jobs possibly needing follow-up", "status='applied'")]
    con=repo.con(); lines=["# Latest Job Report", ""]
    for title, where in sections:
        lines += [f"## {title}", ""]
        rows=con.execute(f"SELECT id,company,title,location,priority,fit_score,status FROM jobs WHERE {where} ORDER BY updated_at DESC LIMIT 20").fetchall()
        if not rows: lines.append("No jobs.")
        for r in rows: lines.append(f"- #{r['id']} **{r['company']}** — {r['title']} ({r['location'] or 'unknown'}) [{r['status']}, {r['priority'] or 'unscored'}, {r['fit_score'] if r['fit_score'] is not None else 'n/a'}]")
        lines.append("")
    lines += ["## Source health summary", ""]
    runs=con.execute("SELECT source,status,jobs_seen,jobs_new,jobs_changed,error FROM source_runs ORDER BY started_at DESC LIMIT 10").fetchall()
    if not runs: lines.append("No source runs recorded.")
    for r in runs: lines.append(f"- {r['source']}: {r['status']} seen={r['jobs_seen']} new={r['jobs_new']} changed={r['jobs_changed']} {r['error'] or ''}")
    lines += ["", "## Recent user decisions", ""]
    ev=repo.events(20)
    if not ev: lines.append("No events recorded.")
    for e in ev: lines.append(f"- {e['event_at']} job #{e['job_id']}: {e['event_type']} {e['note'] or ''}")
    con.close(); return "\n".join(lines)+"\n"
