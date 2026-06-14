from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from jobsearch.db.migrate import connect
from jobsearch.models import NormalizedJob, STATUSES
from jobsearch.normalize.canonicalize import canonical_key, content_hash

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def rowdict(r): return dict(r) if r else None

class Repository:
    def __init__(self, db_path="data/jobs.sqlite"):
        self.db_path = db_path
    def con(self): return connect(self.db_path)
    def add_event(self, con, job_id:int, event_type:str, note:str|None=None, metadata:dict|None=None):
        con.execute("INSERT INTO job_events(job_id,event_type,event_at,note,metadata_json) VALUES(?,?,?,?,?)", (job_id,event_type,now(),note,json.dumps(metadata or {})))
    def upsert_job(self, job: NormalizedJob):
        key, h, ts = canonical_key(job), content_hash(job), now()
        con = self.con(); cur = con.execute("SELECT * FROM jobs WHERE canonical_key=? OR (source_job_id IS NOT NULL AND source=? AND source_job_id=?) OR apply_url=?", (key, job.source, job.source_job_id, job.apply_url)); existing=cur.fetchone()
        if not existing:
            vals=(key,job.company,job.title,job.location,job.remote_type,job.seniority,job.employment_type,job.compensation_min,job.compensation_max,job.compensation_currency,job.apply_url,job.source,job.source_job_id,job.description,ts,ts,h,ts,ts)
            cur=con.execute("""INSERT INTO jobs(canonical_key,company,title,location,remote_type,seniority,employment_type,compensation_min,compensation_max,compensation_currency,apply_url,source,source_job_id,description,first_seen_at,last_seen_at,last_content_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", vals)
            jid=cur.lastrowid; self.add_event(con,jid,"job_created"); self.add_event(con,jid,"job_seen"); changed=True; created=True
        else:
            jid=existing["id"]; created=False; changed=existing["last_content_hash"] != h
            con.execute("UPDATE jobs SET last_seen_at=?, updated_at=? WHERE id=?", (ts,ts,jid))
            if changed:
                con.execute("""UPDATE jobs SET company=?,title=?,location=?,remote_type=?,seniority=?,employment_type=?,compensation_min=?,compensation_max=?,compensation_currency=?,apply_url=?,source=?,source_job_id=?,description=?,last_content_hash=?,updated_at=? WHERE id=?""", (job.company,job.title,job.location,job.remote_type,job.seniority,job.employment_type,job.compensation_min,job.compensation_max,job.compensation_currency,job.apply_url,job.source,job.source_job_id,job.description,h,ts,jid))
                self.add_event(con,jid,"job_changed")
            self.add_event(con,jid,"job_seen")
        if created or changed:
            con.execute("INSERT INTO job_snapshots(job_id,fetched_at,content_hash,raw_excerpt) VALUES(?,?,?,?)", (jid,ts,h,(job.description or json.dumps(job.raw))[:1000]))
        con.commit(); con.close(); return {"job_id":jid,"created":created,"changed":changed}
    def list_jobs(self, status=None, limit=20, order="updated_at DESC"):
        con=self.con(); sql="SELECT * FROM jobs"; args=[]
        if status: sql += " WHERE status=?"; args.append(status)
        sql += f" ORDER BY {order} LIMIT ?"; args.append(limit)
        rows=[dict(r) for r in con.execute(sql,args)]; con.close(); return rows
    def get_job(self, job_id):
        con=self.con(); r=rowdict(con.execute("SELECT * FROM jobs WHERE id=?",(job_id,)).fetchone()); con.close(); return r
    def set_status(self, job_id:int, status:str, event_type="status_changed", note=None):
        if status not in STATUSES: raise ValueError(f"invalid status: {status}")
        con=self.con(); con.execute("UPDATE jobs SET status=?,updated_at=? WHERE id=?",(status,now(),job_id)); self.add_event(con,job_id,event_type,note,{"status":status}); con.commit(); con.close()
    def add_note(self, job_id:int, note:str):
        con=self.con(); self.add_event(con,job_id,"manual_note",note); con.commit(); con.close()
    def source_run_start(self, source):
        con=self.con(); cur=con.execute("INSERT INTO source_runs(source,started_at,status) VALUES(?,?,?)",(source,now(),"running")); con.commit(); rid=cur.lastrowid; con.close(); return rid
    def source_run_finish(self, run_id, status, seen=0,new=0,changed=0,error=None):
        con=self.con(); con.execute("UPDATE source_runs SET finished_at=?,status=?,jobs_seen=?,jobs_new=?,jobs_changed=?,error=? WHERE id=?",(now(),status,seen,new,changed,error,run_id)); con.commit(); con.close()
    def events(self, limit=20):
        con=self.con(); rows=[dict(r) for r in con.execute("SELECT * FROM job_events ORDER BY event_at DESC,id DESC LIMIT ?",(limit,))]; con.close(); return rows
