# Deploying to a Hostinger VPS

This guide covers a clean install on a fresh Hostinger VPS (Ubuntu 22.04 or
24.04). The whole stack runs via Docker Compose — Postgres, Redis, the
FastAPI backend, a Celery worker, and an Nginx-fronted Vue frontend.

## What you need before starting

- A Hostinger VPS plan (KVM 1 / 2 GB RAM minimum; KVM 2 / 4 GB recommended).
- A domain pointed at the VPS public IP (A record `@` and optionally `www`).
  Wait for DNS to propagate before doing the HTTPS step.
- SSH access to the VPS (root or sudo user).
- This repo pushed to a remote you can clone from the VPS (GitHub etc.).

---

## 1. Provision the VPS

In Hostinger's hPanel, create a VPS with Ubuntu 22.04+. Note the public IP.

SSH in:

```bash
ssh root@YOUR_VPS_IP
```

Update + install basics:

```bash
apt update && apt upgrade -y
apt install -y git curl ufw
```

Open the firewall for SSH, HTTP, HTTPS:

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
```

## 2. Install Docker + Docker Compose

Official one-liner:

```bash
curl -fsSL https://get.docker.com | sh
```

Verify:

```bash
docker --version
docker compose version
```

## 3. Clone the repo

```bash
cd /opt
git clone YOUR_REPO_URL mh02
cd mh02
```

## 4. Configure environment variables

Copy the template and edit the secrets:

```bash
cp .env.production .env
nano .env
```

Generate a strong secret key (run on the VPS):

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

`.env` must look like this when you're done (no quotes, no spaces around `=`):

```
DATABASE_URL=postgresql+asyncpg://mh02admin:STRONG_DB_PASSWORD@db:5432/mh02db
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<paste the generated key>
POSTGRES_PASSWORD=STRONG_DB_PASSWORD
```

The `POSTGRES_PASSWORD` value must match the password inside `DATABASE_URL` —
the Postgres container reads it on first boot to set the admin password.

## 5. First boot

Build images and start the stack:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Watch the logs until you see `Application startup complete.`:

```bash
docker compose -f docker-compose.prod.yml logs -f api
```

Press Ctrl+C to detach (containers keep running).

## 6. Create the first admin user

There's no public signup endpoint — bootstrap the admin via the included
script:

```bash
docker compose -f docker-compose.prod.yml exec api \
  python scripts/create_admin.py \
  --name "Your Name" \
  --email "you@yourdomain.com" \
  --password "yourStrongInitialPassword"
```

Test that everything is reachable over plain HTTP first:

```
http://YOUR_VPS_IP/
```

You should see the login page. Log in with the credentials you just created.

## 7. Add HTTPS (Let's Encrypt)

Make sure your domain's DNS A record points to the VPS IP first. Then issue
a certificate:

```bash
docker compose -f docker-compose.prod.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/certbot \
  --email you@yourdomain.com --agree-tos --no-eff-email \
  -d your-domain.com -d www.your-domain.com
```

If you only have the apex domain, drop the second `-d www....` line.

Now activate HTTPS in nginx:

```bash
nano nginx/nginx.conf
```

In that file:
1. Uncomment the redirect block inside the `listen 80` server
   (the three `location /` lines that `return 301 https://...`).
2. Uncomment the entire `server { listen 443 ssl http2; ... }` block at the
   bottom.
3. Replace every `your-domain.com` with your actual domain.

Reload nginx by restarting the frontend container (it mounts the config):

```bash
docker compose -f docker-compose.prod.yml restart frontend
```

Visit `https://your-domain.com/` and confirm the padlock.

The `certbot` container in the compose file auto-renews the cert every 12
hours, so you don't have to think about expiry.

## 8. Operations cheat sheet

```bash
# Tail logs (api / worker / db / frontend)
docker compose -f docker-compose.prod.yml logs -f api

# Restart one service
docker compose -f docker-compose.prod.yml restart api

# Update after pushing new code
cd /opt/mh02
git pull
docker compose -f docker-compose.prod.yml up -d --build

# Open a psql shell
docker compose -f docker-compose.prod.yml exec db \
  psql -U mh02admin -d mh02db

# Backup the database (run on the VPS; rotate to S3 / off-host yourself)
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U mh02admin mh02db | gzip > "backup-$(date +%F).sql.gz"

# Restore from a backup
gunzip < backup-2026-05-25.sql.gz | docker compose -f docker-compose.prod.yml \
  exec -T db psql -U mh02admin -d mh02db
```

## 9. Pitfalls people hit

- **DNS not propagated** — `certbot` will fail with a 404 on the ACME
  challenge. Wait 5-10 minutes and retry. You can sanity-check by visiting
  `http://your-domain.com/.well-known/acme-challenge/anything` — it should
  return a plain 404 from your VPS, not from Hostinger's parking page.
- **DB password mismatch** — if you change `POSTGRES_PASSWORD` after the
  first boot, Postgres won't re-read it (it only initialises on first run).
  Either set the password before the first start, or wipe the volume:
  `docker compose -f docker-compose.prod.yml down -v` (this deletes your
  data — be sure).
- **Bumping into the 2 GB RAM ceiling** — turn off the frontend dev tools,
  and consider bumping to 4 GB. The image build also wants ~1 GB of free
  swap; create some with `fallocate -l 2G /swapfile && chmod 600 /swapfile
  && mkswap /swapfile && swapon /swapfile`.
- **Port 80/443 already in use** — Hostinger's default install may have
  apache or nginx already running. `systemctl stop apache2 nginx && systemctl
  disable apache2 nginx` clears them.

## 10. Optional: demo data

Useful for showing the dashboard / reports to stakeholders before real data
exists. Adds a tagged client, 4 projects, 8 invoices spread across the year,
weekly timesheets, and a few expense rows — all prefixed `DEMO_` so they're
easy to remove later.

```bash
# Copy the seeder into the api container (it's excluded from the prod image)
docker cp backend/scripts/seed_demo_data.py \
  $(docker compose -f docker-compose.prod.yml ps -q api):/app/scripts/

# Run it
docker compose -f docker-compose.prod.yml exec api python scripts/seed_demo_data.py

# Remove it
docker compose -f docker-compose.prod.yml exec api python scripts/seed_demo_data.py --reset
```
