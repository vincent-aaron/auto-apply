# Deployment Guide — Free & Forever

This guide walks you through deploying the **Job Application Automation Assistant** to
**Oracle Cloud's Always-Free** tier — $0, no credit card spend, runs 24/7 indefinitely.

---

## Table of Contents

1. [What "Free" means here](#1-what-free-means-here)
2. [API Key / Secret Inventory](#2-api-key--secret-inventory)
3. [Option A — Manual deploy to an Oracle Cloud VM (simplest)](#3-option-a--manual-deploy-to-an-oracle-cloud-vm-simplest)
4. [Option B — Automated push-to-deploy via GitHub Actions](#4-option-b--automated-push-to-deploy-via-github-actions)
5. [Option C — Local Docker Compose (development)](#5-option-c--local-docker-compose-development)
6. [Post-deployment verification](#6-post-deployment-verification)
7. [Common issues / FAQ](#7-common-issues--faq)

---

## 1. What "Free" means here

| Provider | Resource | Always-Free? | Runs forever? |
|---|---|---|---|
| **Oracle Cloud** | 2× vCPU / 1 GB RAM AMD VM *or* 4× vCPU / 24 GB RAM ARM VM | ✅ Yes | ✅ Yes |
| **GitHub Actions** | 2 000 minutes/month | ✅ Yes (public repo) | ✅ Yes |
| **GitHub Container Registry** | 500 MB storage | ✅ Yes | ✅ Yes |
| **OpenRouter** | `google/gemma-4-31b-it:free` etc. | ✅ Free models | ✅ Yes (rate-limited) |
| **Docker Hub** | public images | ✅ Yes | ✅ Yes |

> **No Fly.io account needed.** All Fly-specific files have been removed.

---

## 2. API Key / Secret Inventory

Only **one** optional API key is needed for optional AI features. Everything
else is **completely free** with no key required.

| Secret / Key | Required? | Free? | Where to get it | Where it goes |
|---|---|---|---|---|
| **`OPENROUTER_API_KEY`** | ❌ Optional (AI features only) | ✅ Free models | [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys) | `.env` file / env var |
| **`OPENROUTER_MODEL`** | ❌ Optional | ✅ Free | Same page | `.env` file / env var |
| **`SECRET_KEY`** | ❌ Optional (falls back to default) | ✅ Free | Any random string | `.env` file / env var |
| **`DATABASE_URL`** | ❌ Optional (falls back to SQLite) | ✅ Free | Built-in SQLite | `.env` file / env var |

**Without `OPENROUTER_API_KEY`**, the app runs with 100 % offline, truthful
local fallback answers. AI is a nice-to-have, not a blocker.

### How to get a free OpenRouter key (3 steps)

1. Go to **[openrouter.ai](https://openrouter.ai)** → sign up (Google/GitHub login, no phone).
2. Visit **https://openrouter.ai/settings/keys** → click **"Create Key"**.
3. Give it a name (e.g. `jobapply`), leave the credit limit at `0`, and **copy** the key (`sk-or-v1-...`).

Then paste it into your `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxx
OPENROUTER_MODEL=google/gemma-4-31b-it:free
```
Restart the app so it's picked up. The AI banner on the dashboard will disappear.

### Free OpenRouter models (pick one)

- `google/gemma-4-31b-it:free` — 262 K context (default)
- `openai/gpt-oss-20b:free` — 131 K context
- `z-ai/glm-5.2:free` — 256 K context
- `nvidia/nemotron-3-super-120b-a12b:free` — 262 K context
- `openrouter/free` — automated "always-free" router (most reliable default)

Set any of these in `.env`: `OPENROUTER_MODEL=<id>`.

---

## 3. Option A — Manual deploy to an Oracle Cloud VM (simplest)

### Step 3.1 — Create a free Oracle Cloud account

1. Go to **[cloud.oracle.com](https://cloud.oracle.com)** and click **"Start for free"**.
2. Fill in your details. Oracle may place a $0 authorization hold on your card — **it is not charged** and falls off in a few days.
3. Verify your email and phone (required for free-tier activation).

### Step 3.2 — Create a free VM

1. In the OCI Console, go to **Compute → Instances** → **"Create Instance"**.
2. **Name**: `autoapply-assistant`
3. **Compartment**: `Always Free`
4. **Image**: Ubuntu 24.04 LTS (or Oracle Linux 9)
5. **Shape**: `VM.Standard.E2.1.Micro` (1 vCPU, 1 GB RAM) — **Always Free**
6. **Add SSH keys**: Create a new pair or paste your existing public key. Save the
   `.pem` private key file somewhere safe.
7. Click **"Create"**. Wait ~1 minute for it to provision.
8. Note the **Public IP** address shown on the instance page.

### Step 3.3 — Open port 8080 in the firewall

1. OCI Console → **Networking → Virtual Cloud Networks** → your VCN →
   **Security Lists** → click the security list for your subnet.
2. **Add Ingress Rule**:
   - **Source CIDR**: `0.0.0.0/0`
   - **Protocol**: `TCP`
   - **Port Range**: `8080`
3. Click **Add Ingress Rules**.

### Step 3.4 — SSH into the VM and deploy

```bash
# On your local machine (or Git Bash / WSL):
ssh -i /path/to/your-key.pem opc@<PUBLIC_IP>
```

Then on the VM:

```bash
# Install Docker if not already present
sudo yum install -y docker || sudo apt-get install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in, or:
newgrp docker

# Make the app directory
mkdir -p /app/data
cd /app

# Copy your .env (or create a minimal one)
cat > /app/.env << 'EOF'
OPENROUTER_API_KEY=  # ← paste your free key here, or leave blank
OPENROUTER_MODEL=google/gemma-4-31b-it:free
DEBUG=False
DATABASE_URL=sqlite:///./data/job_auto_apply.db
EOF

# Pull and run the container
docker run -d \
    --name autoapply-assistant \
    --restart unless-stopped \
    -p 8080:8080 \
    -v /app/data:/app/data \
    --env-file /app/.env \
    ghcr.io/<YOUR_GITHUB_USERNAME>/<YOUR_REPO>:latest

# Check health
curl http://localhost:8080/health
```

> **Or one-liner**: After the first run of Option B at least once, you can
> re-deploy instantly on the VM with:
> ```bash
> curl -fsSL https://raw.githubusercontent.com/<GH_USER>/<REPO>/main/deploy-oci.sh | bash
> ```

---

## 4. Option B — Automated push-to-deploy via GitHub Actions

This sets up CI/CD so every `git push` to `main` automatically rebuilds and
deploys to your OCI VM.

### Step 4.1 — One-time: create the required GitHub Secrets

In your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name | Value |
|---|---|
| `OCI_SSH_HOST` | The public IP of your OCI VM |
| `OCI_SSH_USER` | `opc` (Oracle Linux) or `ubuntu` (Ubuntu) |
| `OCI_SSH_KEY` | Contents of your `.pem` private key file |
| `OPENROUTER_API_KEY` | Your free OpenRouter key (leave empty for offline AI) |

### Step 4.2 — Push and watch it deploy

```bash
git add .
git commit -m "Set up Oracle Cloud deployment"
git push origin main
```

Then visit:
- **Actions** tab → watch the `Deploy to Oracle Cloud` workflow run.
- `http://<YOUR_VM_PUBLIC_IP>:8080/health` → should return `{"status":"healthy",...}`.

---

## 5. Option C — Local Docker Compose (development)

A `docker-compose.yml` is provided for local development with hot-reload:

```bash
cp .env.example .env
# Edit .env — add your OpenRouter key if desired
docker compose up --build
# App: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## 6. Post-deployment verification

```bash
# Health check
curl http://<VM_IP>:8080/health
# Expected: {"status":"healthy","version":"0.1.0","debug":false}

# Config (check AI is wired up)
curl http://<VM_IP>:8080/api/config
# Expected: {"enabled_sources":[...], "ai":{"enabled":true, "model":"google/gemma-4-31b-it:free", ...}}

# Open in browser
http://<VM_IP>:8080/
```

---

## 7. Common issues / FAQ

| Problem | Fix |
|---|---|
| **"Connection refused" after deploy** | Check OCI Security List — did you add the Ingress rule for TCP 8080? |
| **"Permission denied" on Docker** | Run `sudo usermod -aG docker $USER` on the VM, then `newgrp docker`. |
| **Port 8080 conflicts** | Edit `deploy-oci.sh` or the workflow to use a different host port. |
| **AI still shows "local fallback"** | Make sure `.env` has `OPENROUTER_API_KEY=sk-or-v1-...` and restart the container. |
| **Container won't start** | Run `docker logs autoapply-assistant` on the VM to see the error. |
| **Need HTTPS** | Add a Caddy/Traefik reverse proxy or use a Cloudflare Tunnel (both free). |
| **Larger disk** | OCI Always-Free includes 200 GB block storage. You can attach more via OCI Console. |

---

## Files changed for this migration

| File | Action |
|---|---|
| ~~`fly.toml`~~ | ❌ Removed |
| ~~`deploy-fly.ps1`~~ | ❌ Removed |
| ~~`.github/workflows/fly-deploy.yml`~~ | ❌ Removed |
| `Dockerfile` | ✅ Comment updated (no Fly references) |
| `.dockerignore` | ✅ `fly.toml` entry removed |
| `.github/workflows/oci-deploy.yml` | ✅ New — GitHub Actions → OCI |
| `deploy-oci.sh` | ✅ New — one-liner VM deploy script |
| `DEPLOYMENT.md` | ✅ New — this guide |
| `README.md` | ✅ Docker & Cloud marked as ✅ implemented |

