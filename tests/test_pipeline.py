import json
from pathlib import Path
from jobsearch.db.migrate import migrate
from jobsearch.db.repository import Repository
from jobsearch.models import RawJob
from jobsearch.normalize.canonicalize import canonical_company, canonical_title, canonical_location, normalize_raw_job
from jobsearch.tasks.export import export_tasks
from jobsearch.tasks.import_results import import_results
from jobsearch.reports.markdown import generate_markdown

def test_canonicalize():
    assert canonical_company('Example, Inc.') == 'example'
    assert canonical_title('Senior/Staff ML Engineer') == 'senior staff ml engineer'
    assert canonical_location('San Francisco, CA') == 'san francisco'

def test_dedupe_and_status_persistence(tmp_path):
    db=tmp_path/'x.sqlite'; migrate(db); repo=Repository(db)
    raw=RawJob('Example Inc.','Staff ML Engineer','https://e.com/jobs/1?utm_source=x','greenhouse','1','Remote','desc')
    a=repo.upsert_job(normalize_raw_job(raw)); b=repo.upsert_job(normalize_raw_job(raw))
    assert a['created'] is True and b['created'] is False
    repo.set_status(a['job_id'],'discarded','user_discarded','no')
    repo.upsert_job(normalize_raw_job(raw))
    assert repo.get_job(a['job_id'])['status'] == 'discarded'

def test_changed_content_snapshot_event(tmp_path):
    db=tmp_path/'x.sqlite'; migrate(db); repo=Repository(db)
    raw=RawJob('Example','Staff ML Engineer','https://e.com/jobs/1','lever','1','Remote','desc')
    jid=repo.upsert_job(normalize_raw_job(raw))['job_id']
    raw.description='new desc'
    assert repo.upsert_job(normalize_raw_job(raw))['changed'] is True
    con=repo.con(); assert con.execute("SELECT COUNT(*) c FROM job_snapshots WHERE job_id=?",(jid,)).fetchone()['c'] == 2
    assert con.execute("SELECT COUNT(*) c FROM job_events WHERE event_type='job_changed'").fetchone()['c'] == 1

def test_task_export_import_and_bad_rows(tmp_path):
    db=tmp_path/'x.sqlite'; out=tmp_path/'tasks.jsonl'; res=tmp_path/'results.jsonl'; migrate(db); repo=Repository(db)
    jid=repo.upsert_job(normalize_raw_job(RawJob('Example','Staff ML Engineer','https://e.com/jobs/1','lever','1','Remote','desc')))['job_id']
    assert export_tasks(out, 5, {'profile':{}}, db) == 1
    task=json.loads(out.read_text().splitlines()[0])
    res.write_text(json.dumps({'task_id':task['task_id'],'job_id':jid,'fit_score':88,'priority':'high','summary':'Good','concerns':[],'tags':['ml'],'suggested_status':'reviewed'})+'\n'+json.dumps({'task_id':'bad','job_id':jid,'fit_score':999,'priority':'high','summary':'x'})+'\n')
    result=import_results(res, db)
    assert result['imported'] == 1 and len(result['errors']) == 1
    job=repo.get_job(jid); assert job['fit_score'] == 88 and job['priority'] == 'high' and job['status'] == 'reviewed'

def test_empty_report(tmp_path):
    db=tmp_path/'x.sqlite'; migrate(db)
    assert 'Latest Job Report' in generate_markdown(db)
