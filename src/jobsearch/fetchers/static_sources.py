from jobsearch.models import RawJob
class CustomURLFetcher:
    name="custom_urls"
    def fetch(self, config):
        import requests
        jobs=[]; timeout=config.get("runtime",{}).get("request_timeout_seconds",30)
        for item in config.get("sources",{}).get("custom_urls",{}).get("urls",[]):
            r=requests.get(item["url"],timeout=timeout); r.raise_for_status()
            jobs.append(RawJob(company=item.get("name","Custom Source"), title=f"Review source: {item.get('name','custom')}", apply_url=item["url"], source=self.name, source_job_id=item["url"], location=None, description=r.text[:4000], raw={"status_code":r.status_code,"url":item["url"]}))
        return jobs
