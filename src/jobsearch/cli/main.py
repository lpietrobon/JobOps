from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from jobsearch.config import load_config
from jobsearch.db.migrate import migrate
from jobsearch.db.repository import Repository
from jobsearch.fetchers import FETCHERS
from jobsearch.normalize.canonicalize import normalize_raw_job
from jobsearch.tasks.export import export_tasks
from jobsearch.tasks.import_results import import_results
from jobsearch.reports.markdown import generate_markdown
from jobsearch.reports.html import generate_html

DB="data/jobs.sqlite"

def print_rows(rows, as_json=False):
    if as_json: print(json.dumps(rows, indent=2)); return
    for j in rows: print(f"#{j['id']} {j['status']} {j['company']} — {j['title']} ({j.get('priority') or 'unscored'} {j.get('fit_score') if j.get('fit_score') is not None else ''})")

def ingest_command(source=None):
    cfg=load_config(); repo=Repository(DB); names=[source] if source else list(FETCHERS)
    successes=failures=0
    for name in names:
        src_cfg=cfg.get("sources",{}).get(name,{})
        if src_cfg and not src_cfg.get("enabled", True): continue
        run=repo.source_run_start(name); seen=new=changed=0
        try:
            raws=FETCHERS[name].fetch(cfg); seen=len(raws)
            for raw in raws:
                res=repo.upsert_job(normalize_raw_job(raw)); new += int(res["created"]); changed += int(res["changed"] and not res["created"])
            repo.source_run_finish(run,"ok",seen,new,changed); successes+=1
        except Exception as e:
            repo.source_run_finish(run,"error",seen,new,changed,str(e)); failures+=1; print(f"source {name} failed: {e}", file=sys.stderr)
    if successes==0 and failures>0: raise SystemExit(1)

def build_parser():
    p=argparse.ArgumentParser(prog="jobctl"); sub=p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init-db"); sub.add_parser("migrate"); sub.add_parser("config-check")
    ip=sub.add_parser("ingest"); ip.add_argument("--source", choices=list(FETCHERS))
    ep=sub.add_parser("export-classification-tasks"); ep.add_argument("--limit", type=int, default=50); ep.add_argument("--out", required=True)
    imp=sub.add_parser("import-classifications"); imp.add_argument("path")
    for cmd in ["latest","top","saved","discarded","source-health"]:
        sp=sub.add_parser(cmd); sp.add_argument("--limit", type=int, default=20); sp.add_argument("--json", action="store_true")
    ap=sub.add_parser("applied"); ap.add_argument("job_id", nargs="?", type=int); ap.add_argument("--json", action="store_true"); ap.add_argument("--limit", type=int, default=20)
    sh=sub.add_parser("show"); sh.add_argument("job_id", type=int); sh.add_argument("--json", action="store_true")
    st=sub.add_parser("stats"); st.add_argument("--since", default="30d"); st.add_argument("--json", action="store_true")
    for cmd in ["save","reject"]:
        sp=sub.add_parser(cmd); sp.add_argument("job_id", type=int); sp.add_argument("--reason")
    dp=sub.add_parser("discard"); dp.add_argument("job_id", type=int); dp.add_argument("--reason")
    sp=sub.add_parser("status"); sp.add_argument("job_id", type=int); sp.add_argument("status")
    nt=sub.add_parser("note"); nt.add_argument("job_id", type=int); nt.add_argument("note")
    rp=sub.add_parser("report"); rp.add_argument("--format", choices=["md","html","both"], default="both")
    return p

def main(argv=None):
    args=build_parser().parse_args(argv); repo=Repository(DB)
    if args.cmd in {"init-db","migrate"}: migrate(DB); print(f"initialized {DB}")
    elif args.cmd=="config-check": cfg=load_config(); print(json.dumps({"ok": True, "sources": list(cfg.get("sources",{}))}, indent=2))
    elif args.cmd=="ingest": migrate(DB); ingest_command(args.source)
    elif args.cmd=="export-classification-tasks": migrate(DB); print(export_tasks(args.out,args.limit,load_config(),DB))
    elif args.cmd=="import-classifications": migrate(DB); print(json.dumps(import_results(args.path,DB), indent=2))
    elif args.cmd=="latest": print_rows(repo.list_jobs(limit=args.limit), args.json)
    elif args.cmd=="top": print_rows(repo.list_jobs(limit=args.limit, order="fit_score DESC, updated_at DESC"), args.json)
    elif args.cmd in {"saved","discarded"}: print_rows(repo.list_jobs(status=args.cmd, limit=args.limit), args.json)
    elif args.cmd=="applied" and args.job_id: repo.set_status(args.job_id,"applied","user_applied")
    elif args.cmd=="applied": print_rows(repo.list_jobs(status="applied", limit=args.limit), args.json)
    elif args.cmd=="show": obj=repo.get_job(args.job_id); print(json.dumps(obj, indent=2) if args.json else obj)
    elif args.cmd=="save": repo.set_status(args.job_id,"saved","user_saved",args.reason)
    elif args.cmd=="discard": repo.set_status(args.job_id,"discarded","user_discarded",args.reason)
    elif args.cmd=="reject": repo.set_status(args.job_id,"rejected","user_rejected",args.reason)
    elif args.cmd=="status": repo.set_status(args.job_id,args.status,"status_changed")
    elif args.cmd=="note": repo.add_note(args.job_id,args.note)
    elif args.cmd=="stats":
        con=repo.con(); rows=[dict(r) for r in con.execute("SELECT status, COUNT(*) count FROM jobs GROUP BY status")]; con.close(); print(json.dumps(rows, indent=2) if args.json else rows)
    elif args.cmd=="source-health":
        con=repo.con(); rows=[dict(r) for r in con.execute("SELECT * FROM source_runs ORDER BY started_at DESC LIMIT ?",(args.limit,))]; con.close(); print(json.dumps(rows, indent=2) if args.json else rows)
    elif args.cmd=="report":
        Path("reports").mkdir(exist_ok=True)
        if args.format in {"md","both"}: Path("reports/latest.md").write_text(generate_markdown(DB))
        if args.format in {"html","both"}: Path("reports/latest.html").write_text(generate_html(DB))
        print("wrote reports/latest.md and/or reports/latest.html")
if __name__ == "__main__": main()
