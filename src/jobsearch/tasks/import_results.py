import json
from jobsearch.db.repository import Repository, now
from jobsearch.models import PRIORITIES, STATUSES

def validate(obj):
    if not isinstance(obj.get("task_id"), str) or not obj["task_id"]: return "invalid task_id"
    if not isinstance(obj.get("job_id"), int): return "invalid job_id"
    score=obj.get("fit_score")
    if not isinstance(score,(int,float)) or score < 0 or score > 100: return "invalid fit_score"
    if obj.get("priority") not in PRIORITIES: return "invalid priority"
    if not isinstance(obj.get("summary"), str): return "invalid summary"
    if not isinstance(obj.get("concerns",[]), list) or not isinstance(obj.get("tags",[]), list): return "invalid list fields"
    ss=obj.get("suggested_status")
    if ss is not None and ss not in {"new","reviewed","saved","discarded"}: return "invalid suggested_status"
    return None

def import_results(path, db_path="data/jobs.sqlite"):
    repo=Repository(db_path); imported=0; errors=[]; con=repo.con()
    with open(path) as fh:
        for lineno,line in enumerate(fh,1):
            try: obj=json.loads(line)
            except Exception as e: errors.append({"line":lineno,"error":f"malformed json: {e}"}); continue
            err=validate(obj)
            if err: errors.append({"line":lineno,"error":err}); continue
            if not con.execute("SELECT id FROM jobs WHERE id=?",(obj["job_id"],)).fetchone(): errors.append({"line":lineno,"error":"job not found"}); continue
            con.execute("UPDATE jobs SET fit_score=?, priority=?, summary=?, concerns_json=?, tags_json=?, updated_at=? WHERE id=?",(obj["fit_score"],obj["priority"],obj["summary"],json.dumps(obj.get("concerns",[])),json.dumps(obj.get("tags",[])),now(),obj["job_id"]))
            repo.add_event(con,obj["job_id"],"classification_imported",metadata={"task_id":obj["task_id"]})
            con.execute("UPDATE classification_tasks SET imported_at=?, status='imported' WHERE task_id=?",(now(),obj["task_id"]))
            if obj.get("suggested_status") == "reviewed":
                con.execute("UPDATE jobs SET status='reviewed' WHERE id=? AND status='new'",(obj["job_id"],))
            imported+=1
    con.commit(); con.close(); return {"imported":imported,"errors":errors}
