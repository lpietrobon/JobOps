from jobsearch.models import RawJob
class GreenhouseFetcher:
    name="greenhouse"
    def fetch(self, config):
        import requests
        jobs=[]; timeout=config.get("runtime",{}).get("request_timeout_seconds",30)
        for company in config.get("sources",{}).get("greenhouse",{}).get("companies",[]):
            data=requests.get(f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true",timeout=timeout).json()
            for j in data.get("jobs",[]):
                loc=(j.get("location") or {}).get("name")
                jobs.append(RawJob(company=company,title=j.get("title",""),apply_url=j.get("absolute_url",""),source=self.name,source_job_id=str(j.get("id")),location=loc,description=j.get("content"),raw=j))
        return jobs
