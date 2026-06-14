from jobsearch.models import RawJob
class AshbyFetcher:
    name="ashby"
    def fetch(self, config):
        import requests
        jobs=[]; timeout=config.get("runtime",{}).get("request_timeout_seconds",30)
        for company in config.get("sources",{}).get("ashby",{}).get("companies",[]):
            data=requests.get(f"https://api.ashbyhq.com/posting-api/job-board/{company}",timeout=timeout).json()
            for j in data.get("jobs",[]):
                jobs.append(RawJob(company=company,title=j.get("title",""),apply_url=j.get("jobUrl",""),source=self.name,source_job_id=j.get("id"),location=j.get("location"),description=j.get("descriptionPlain"),raw=j))
        return jobs
