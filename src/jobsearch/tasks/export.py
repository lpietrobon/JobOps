import json
from pathlib import Path
from datetime import datetime, timezone
from jobsearch.db.repository import Repository, now

SCHEMA={"task_id":"string","job_id":"integer","fit_score":"integer 0-100","priority":"high|medium|low","summary":"string","concerns":["string"],"tags":["string"],"suggested_status":"new|reviewed|saved|discarded|null"}

def export_tasks(out, limit=50, config=None, db_path="data/jobs.sqlite"):
    repo=Repository(db_path); jobs=repo.list_jobs(limit=limit, order="COALESCE(fit_score,-1) ASC, updated_at DESC")
    Path(out).parent.mkdir(parents=True, exist_ok=True); count=0
    profile=(config or {}).get("profile",{})
    con=repo.con()
    with open(out,"w") as fh:
        for j in jobs:
            if j.get("status") not in ("new","reviewed"): continue
            task_id=f"classify_job_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{j['id']:06d}"
            obj={"task_id":task_id,"job_id":j["id"],"company":j["company"],"title":j["title"],"location":j["location"],"source":j["source"],"apply_url":j["apply_url"],"description":(j.get("description") or "")[:4000],"known_fields":{"seniority":j.get("seniority"),"compensation_min":j.get("compensation_min"),"compensation_max":j.get("compensation_max"),"remote_type":j.get("remote_type")},"user_preferences":{"target_roles":profile.get("target_roles",[]),"negative_keywords":profile.get("negative_keywords",[]),"accepted_locations":profile.get("locations",{}).get("accepted",[])},"required_output_schema":SCHEMA}
            fh.write(json.dumps(obj)+"\n"); count+=1
            con.execute("INSERT OR IGNORE INTO classification_tasks(task_id,job_id,exported_at,output_path) VALUES(?,?,?,?)",(task_id,j["id"],now(),str(out)))
    con.commit(); con.close(); return count
