# Hosting the live prototype

The API (`api.py`) also serves the prototype page itself at `/`, so one deployed service is
the whole demo -- no separate frontend hosting needed. The HTML auto-detects whether it's
running locally (`file://`) or served by the API (calls its own origin), so nothing needs to
change between local testing and a deployed copy.

## Fastest option: Render.com (free tier, no credit card)

1. Push this `churn_prototype/` folder to a GitHub repo (can be a new, private one).
2. Go to render.com, sign up / log in, click **New +** -> **Web Service**.
3. Connect the repo. Render will detect the `Dockerfile` automatically.
4. Leave the build/start commands blank (the Dockerfile handles both). Instance type: **Free**.
5. Click **Create Web Service**. First build takes a few minutes.
6. Once live, Render gives you a URL like `https://churn-risk-scoring.onrender.com` -- that's
   the whole demo, calculator and ranked list included.

Free-tier instances sleep after inactivity and take ~30-50 seconds to wake on the first
request -- fine for a graded demo, just don't expect an instant response after idling.

## Alternative: Railway.app or Fly.io

Both also build directly from the `Dockerfile` with no changes needed:
- Railway: `railway login`, then `railway init` and `railway up` from this folder.
- Fly.io: `fly launch` (it reads the Dockerfile), then `fly deploy`.

## If you'd rather I drive the deployment

I can't create a hosting account on your behalf, but once you've signed up and generated an
API token (Render, Railway, and Fly.io all support CLI/API deploys with a token), hand me the
token and I can run the deploy commands directly from here.

## Testing the Docker build locally (optional, needs Docker Desktop installed)

```
docker build -t churn-risk-api .
docker run -p 8000:8000 churn-risk-api
```

Then open http://localhost:8000 in a browser -- same page, same live model, no `file://` and
no need to run `uvicorn` separately.
