from jobsearch.models import NormalizedJob
from jobsearch.normalize.canonicalize import canonical_key

def job_key(job: NormalizedJob) -> str:
    return canonical_key(job)
