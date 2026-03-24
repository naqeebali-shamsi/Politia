# Politia Deployment Guide

## Step 1: Create GitHub Repository

```bash
cd N:\Politia
git add -A
git commit -m "Initial commit: Politia MVP - Indian MP Accountability Dashboard"
gh repo create Politia --public --source=. --push
```

## Step 2: Set Up Neon PostgreSQL (Free)

1. Go to https://neon.tech and sign up (free)
2. Create a new project named "politia"
3. Copy the connection string (looks like: `postgresql://user:pass@ep-xxx.neon.tech/politia?sslmode=require`)
4. Update backend/.env:
   ```
   POLITIA_DATABASE_URL=postgresql+psycopg://user:pass@ep-xxx.neon.tech/politia?sslmode=require
   ```
5. Run the ingestion pipeline:
   ```bash
   cd backend
   python -m scripts.ingest
   ```

## Step 3: Deploy Backend to Render (Free)

1. Go to https://render.com and connect your GitHub
2. Create a new "Web Service" from the Politia repo
3. Set:
   - Root directory: `backend`
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable:
   - `POLITIA_DATABASE_URL` = your Neon connection string
   - `POLITIA_CORS_ORIGINS` = `["https://politia.vercel.app","http://localhost:3000"]`
5. Deploy

## Step 4: Deploy Frontend to Vercel (Free)

```bash
cd frontend
vercel --prod
```

When prompted, set environment variable:
- `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g., https://politia-api.onrender.com)
