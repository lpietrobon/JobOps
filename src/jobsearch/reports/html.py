import html
from jobsearch.reports.markdown import generate_markdown

def generate_html(db_path="data/jobs.sqlite"):
    md=generate_markdown(db_path)
    body="\n".join(f"<p>{html.escape(line)}</p>" if line and not line.startswith('#') else f"<h{min(line.count('#'),6)}>{html.escape(line.lstrip('# '))}</h{min(line.count('#'),6)}>" for line in md.splitlines())
    return "<!doctype html><html><head><meta charset='utf-8'><title>Job Report</title></head><body>"+body+"</body></html>"
