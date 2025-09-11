import os, sys, json, urllib.request
token = os.environ.get("GH_TOKEN")
if not token: raise SystemExit("GH_TOKEN env var required")
owner, repo, branch = sys.argv[1], sys.argv[2], sys.argv[3]  # branch='master'
url = f"https://api.github.com/repos/{owner}/{repo}/branches/{branch}/protection"
payload = {
  "required_status_checks": {"strict": True, "contexts": ["PR Validate (Build/Test/Lint/DB + Auto Report)"]},
  "enforce_admins": True,
  "required_pull_request_reviews": {"dismiss_stale_reviews": True, "require_code_owner_reviews": False, "required_approving_review_count": 1},
  "restrictions": None
}
req = urllib.request.Request(url, method="PUT",
  headers={"Authorization": f"Bearer {token}", "Accept":"application/vnd.github+json","Content-Type":"application/json"},
  data=json.dumps(payload).encode())
with urllib.request.urlopen(req) as r:
  print("Status:", r.status)
  print(r.read().decode())