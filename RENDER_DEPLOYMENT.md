# Render Deployment Guide

This guide covers deploying the IDS application to Render.com, a cloud platform that simplifies deploying web services and databases.

## Prerequisites

- Render account (free tier available)
- GitHub account with the application code
- Basic understanding of Git

## Step 1: Prepare Your Code

### Ensure Files Are Committed

Make sure all files are committed to your Git repository:

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Required Files

Your repository should include:
- `render.yaml` - Render configuration
- `requirements.txt` - Python dependencies
- `wsgi.py` - WSGI entry point
- `.env.example` - Environment variables template
- All application code and templates

## Step 2: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Authorize Render to access your repositories

## Step 3: Deploy PostgreSQL Database

### Create PostgreSQL Instance

1. Go to Render Dashboard → New → PostgreSQL
2. Configure:
   - **Name**: `ids-db`
   - **Database**: `ids_db`
   - **User**: `ids_user`
   - **Region**: Choose nearest region
   - **Plan**: Free (for testing) or paid for production
3. Click "Create Database"

### Get Database Connection String

After creation, Render will provide:
- Internal Database URL (for Render services)
- External Database URL (for external connections)

Copy the **Internal Database URL** - this will be automatically set as `DATABASE_URL` environment variable.

## Step 4: Deploy Web Service

### Create Web Service

1. Go to Render Dashboard → New → Web Service
2. Connect your GitHub repository
3. Configure:
   - **Name**: `ids-app`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
   - **Instance Type**: Free (for testing) or paid for production

### Add Environment Variables

In the "Advanced" section, add these environment variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Production mode |
| `SECRET_KEY` | `[generate-secret]` | Flask secret key |
| `API_KEY` | `[generate-secret]` | API authentication key |
| `DATABASE_URL` | `[auto-filled]` | Auto-filled by Render |

**Generate Secrets:**
```bash
python generate_secrets.py
```
Use the generated values for SECRET_KEY and API_KEY.

### Connect to Database

1. Scroll to "Databases" section
2. Select your PostgreSQL instance (`ids-db`)
3. This automatically sets `DATABASE_URL` environment variable

### Deploy

Click "Create Web Service". Render will:
- Clone your repository
- Install dependencies
- Build the application
- Start the Gunicorn server

## Step 5: Configure Domain (Optional)

### Default Domain

Render provides a default URL:
```
https://ids-app.onrender.com
```

### Custom Domain

1. Go to your web service settings
2. Click "Domains"
3. Add your custom domain (e.g., `ids.yourdomain.com`)
4. Update DNS records as instructed by Render
5. Render will automatically provision SSL certificate

## Step 6: Initialize Database

The database tables will be created automatically when the application starts. However, you may want to verify:

### Access Render Shell

1. Go to your web service
2. Click "Shell" (top right)
3. Run:
```bash
python -c "from core.database import db; print('Database initialized')"
```

### Create Admin User

In the shell:
```python
from core.auth import bcrypt
from core.database import db

# Create admin user
password_hash = bcrypt.generate_password_hash('your-secure-password').decode('utf-8')
db.create_user('admin', password_hash)
print('Admin user created')
```

## Step 7: Monitor Deployment

### View Logs

1. Go to your web service
2. Click "Logs" tab
3. Monitor for errors or warnings

### Check Status

- The service should show "Live" status
- Click the URL to access your application

## Step 8: Configure Session Storage

Render's file system is ephemeral. For persistent sessions, consider using Redis:

### Add Redis (Optional)

1. Create Redis instance in Render
2. Add `DATABASE_URL` for Redis
3. Update `SESSION_TYPE` to `redis` in environment variables

For now, filesystem sessions work but sessions will be lost on redeploy.

## Troubleshooting

### Build Failures

**Issue**: Dependencies fail to install
```bash
# Check logs for specific error
# Ensure requirements.txt has correct versions
```

**Issue**: Python version mismatch
```bash
# Ensure render.yaml specifies correct Python version
runtime: python
pythonVersion: 3.9.0
```

### Database Connection Issues

**Issue**: Cannot connect to database
```bash
# Verify DATABASE_URL is set
# Check database is in same region as web service
# Ensure database is not paused (free tier pauses after inactivity)
```

### Application Won't Start

**Issue**: Gunicorn fails to start
```bash
# Check start command: gunicorn wsgi:app
# Verify wsgi.py exists and is correct
# Check logs for specific error
```

### Session Issues

**Issue**: Users logged out frequently
- This is expected with filesystem sessions on Render
- Consider implementing Redis for persistent sessions

## Free Tier Limitations

Render's free tier has limitations:

- **Web Service**: Spins down after 15 minutes of inactivity (cold starts)
- **Database**: Spins down after 90 days of inactivity
- **File System**: Ephemeral - changes lost on redeploy
- **Session Storage**: Filesystem sessions lost on redeploy

For production, consider:
- Paid instance for web service (keeps running)
- Paid database instance (no spin-down)
- Redis for session storage
- Object storage for persistent files

## Scaling

### Horizontal Scaling

1. Go to web service settings
2. Increase instances (requires paid plan)
3. Render will load balance across instances

### Vertical Scaling

1. Upgrade to larger instance type
2. More CPU and memory

## Monitoring

### Render Dashboard

- Monitor CPU, memory, and response times
- View logs in real-time
- Set up alerts for errors

### Application Monitoring

Consider integrating:
- Sentry for error tracking
- LogRocket for session replay
- New Relic for APM

## Backup Strategy

### Database Backups

Render automatically backs up PostgreSQL:
- Daily backups retained for 7 days (free tier)
- Manual backups available in database settings

### Export Database

```bash
# From Render shell
pg_dump $DATABASE_URL > backup.sql
```

### Import Database

```bash
# From Render shell
psql $DATABASE_URL < backup.sql
```

## Security Best Practices

1. **Environment Variables**: Never commit secrets to Git
2. **HTTPS**: Render automatically provisions SSL
3. **Database**: Use internal URLs for service-to-service communication
4. **API Keys**: Rotate keys regularly
5. **Dependencies**: Keep dependencies updated

## CI/CD

### Automatic Deployments

Render automatically deploys when you push to the connected branch.

### Manual Deployments

1. Go to web service
2. Click "Manual Deploy"
3. Select branch and commit

### Disable Auto-Deploy

1. Go to web service settings
2. Disable "Auto-Deploy"

## Cost Estimation

### Free Tier (Monthly)
- Web Service: $0 (with limitations)
- PostgreSQL: $0 (with limitations)
- **Total**: $0

### Starter Tier (Monthly)
- Web Service: $7
- PostgreSQL: $7
- **Total**: ~$14

### Production Tier
- Depends on traffic and resource requirements
- Estimate $50-200/month for moderate traffic

## Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] Database connection working
- [ ] User authentication functional
- [ ] API endpoints responding
- [ ] Static files loading correctly
- [ ] Logs being written
- [ ] Admin user created
- [ ] Session persistence configured (if needed)
- [ ] Monitoring configured
- [ ] Backup strategy in place

## Alternative: Using render.yaml

The `render.yaml` file in your repository allows you to define infrastructure as code:

```yaml
services:
  - type: web
    name: ids-app
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn wsgi:app
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PYTHON_VERSION
        value: 3.9.0

databases:
  - name: ids-db
    databaseName: ids_db
    user: ids_user
    plan: free
```

To use this:
1. Commit `render.yaml` to your repository
2. In Render, click "New" → "Blueprint"
3. Connect your repository
4. Render will create resources based on the YAML

## Support

- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com
- Render Status: https://status.render.com
