# Production Configuration Guide

This document describes how to run the Aksjeradar application in a real production environment with clear separation between development and production settings.

## 1. Environment Selection

Set exactly one of the following (APP_ENV takes priority):

- APP_ENV=production (recommended) 
- FLASK_ENV=production (legacy fallback)

Supported values: development, testing, production.

## 2. Required Environment Variables
Copy `.env.example` to `.env` locally or add these to your hosting provider:

| Variable | Description |
|----------|-------------|
| APP_ENV | Selects config profile (production/dev/testing) |
| SECRET_KEY | Flask session signing key (generate securely) |
| WTF_CSRF_SECRET_KEY | CSRF protection key |
| DATABASE_URL | Production database URL (PostgreSQL recommended) |
| STRIPE_SECRET_KEY | Stripe live secret key |
| STRIPE_PUBLISHABLE_KEY | Stripe live publishable key |
| STRIPE_WEBHOOK_SECRET | Stripe webhook signing secret |
| STRIPE_*_PRICE_ID | Price IDs for billing tiers |
| REDIS_URL | Redis instance for caching / rate limiting |
| MAIL_* | SMTP credentials (if email features enabled) |
| FMP_API_KEY etc. | External market data API keys |

## 3. Security Checklist

- Use strong random values for SECRET_KEY & WTF_CSRF_SECRET_KEY.
- Ensure SESSION_COOKIE_SECURE=True behind HTTPS.
- Set PREFERRED_URL_SCHEME=https.
- Disable DEBUG in production (APP_ENV=production does this automatically).
- Restrict database credentials with least privilege.
- Rotate API keys periodically.

## 4. Running in Production

Example (Gunicorn + gevent):
```
APP_ENV=production gunicorn -w 4 -k gevent --timeout 120 wsgi:app
```

Systemd unit example (snippet):
```
[Service]
Environment="APP_ENV=production"
WorkingDirectory=/opt/aksjeradar
ExecStart=/usr/bin/env gunicorn -w 4 -k gevent --timeout 120 wsgi:app
Restart=always
User=www-data
Group=www-data
```

## 5. Database Migrations

Use Flask-Migrate (already integrated):
```
flask db migrate -m "Description"
flask db upgrade
```
Ensure the `FLASK_APP` environment variable points to `wsgi:app` or the factory pattern is discoverable via `app`.

## 6. Caching & Rate Limiting

Set `REDIS_URL` to an external managed Redis service for persistence & performance.
Fallback cache is in-memory (simple) which is not suitable for multi-instance deployments.

## 7. Stripe Webhooks

Expose webhook endpoint (check existing blueprint for path). Use something like:
```
stripe listen --forward-to localhost:5000/stripe/webhook
```
In production add the real endpoint to Stripe dashboard.

## 8. Logging

Use Gunicorn access/error logs. For structured logging consider enabling JSON log format in a future improvement.

## 9. Health & Monitoring

- Implement uptime checks on `/health` route (already present via blueprint). 
- Add external monitoring (Pingdom, UptimeRobot).

## 10. Common Pitfalls

| Issue | Fix |
|-------|-----|
| Using `postgres://` URL | Replace prefix with `postgresql://` |
| DEBUG unexpectedly True | Check overridden env vars or .env lingering from dev |
| Session logout issues | Ensure consistent SECRET_KEY across deployments |
| CSRF errors in production | Verify correct domain & HTTPS, adjust SameSite if using subdomains |

## 11. Verification Steps

After deployment run:
1. Load homepage (no stack traces, correct branding).
2. Register/login (session persists across requests).
3. Create a price alert (stored in DB).
4. Visit portfolio analyzer (real metrics load, no demo overlay if premium).
5. Stripe checkout (test mode) creates session (optional in staging).

## 12. Next Steps / Enhancements

- Add structured logging (JSON) with correlation IDs.
- Centralize demo gating to isolate demo mode strictly to `/demo`.
- Implement feature flag service for staged rollouts.
- Add Sentry or similar error tracking.

---

For questions or operational issues, document incidents in `OPERATIONS_LOG.md` (create if needed).
