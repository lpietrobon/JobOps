from jobsearch.models import RawJob
class LeverFetcher:
    name="lever"
    def fetch(self, config):
        import requests
        jobs=[]; timeout=config.get("runtime",{}).get("request_timeout_seconds",30)
        for company in config.get("sources",{}).get("lever",{}).get("companies",[]):
            data=requests.get(f"https://api.lever.co/v0/postings/{company}?mode=json",timeout=timeout).json()
            for j in data:
                jobs.append(RawJob(company=company,title=j.get("text",""),apply_url=j.get("hostedUrl",""),source=self.name,source_job_id=j.get("id"),location=(j.get("categories") or {}).get("location"),description=j.get("descriptionPlain"),raw=j))
        return jobs
