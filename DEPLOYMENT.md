# Production Deployment Guide

This guide covers deploying the IDS application to a production server using Gunicorn, systemd, and Nginx.

## Prerequisites

- Ubuntu/Debian Linux server
- Python 3.9+
- Root or sudo access
- Domain name configured with DNS

## Step 1: Server Setup

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib certbot python3-certbot-nginx
```

## Step 2: Application Setup

### Clone/Upload Application
```bash
# Clone from git or upload files to /var/www/ids
sudo mkdir -p /var/www/ids
sudo chown $USER:$USER /var/www/ids
# Copy your application files to /var/www/ids
```

### Create Virtual Environment
```bash
cd /var/www/ids
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Generate Production Secrets
```bash
python generate_secrets.py
```

### Configure Environment Variables
```bash
cp .env.example .env
nano .env
```
Update the following values:
- `SECRET_KEY` (use generated value)
- `API_KEY` (use generated value)
- `DATABASE_URL` (PostgreSQL connection string)
- `FLASK_ENV=production`

## Step 3: Database Setup (PostgreSQL)

### Create Database and User
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE ids_db;
CREATE USER ids_user WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE ids_db TO ids_user;
\q
```

### Update .env with Database URL
```
DATABASE_URL=postgresql://ids_user:strong_password_here@localhost/ids_db
```

### Initialize Database
```bash
cd /var/www/ids
source venv/bin/activate
python -c "from core.database import init_db; init_db()"
```

## Step 4: Gunicorn Configuration

### Test Gunicorn
```bash
cd /var/www/ids
source venv/bin/activate
gunicorn --bind 0.0.0.0:5000 wsgi:app
```
Press Ctrl+C to stop.

## Step 5: Systemd Service

### Install Service File
```bash
sudo cp ids.service /etc/systemd/system/
sudo nano /etc/systemd/system/ids.service
```
Update paths if your installation directory differs.

### Start and Enable Service
```bash
sudo systemctl start ids
sudo systemctl enable ids
sudo systemctl status ids
```

## Step 6: Nginx Configuration

### Install Nginx Config
```bash
sudo cp nginx.conf /etc/nginx/sites-available/ids
sudo nano /etc/nginx/sites-available/ids
```
Update `server_name` with your actual domain.

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/ids /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: SSL/HTTPS with Let's Encrypt

### Obtain SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```
Follow the prompts. Certbot will automatically configure SSL.

### Auto-renewal is configured by default:
```bash
sudo certbot renew --dry-run
```

## Step 8: Security Hardening

### Firewall Configuration
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### File Permissions
```bash
sudo chown -R www-data:www-data /var/www/ids
sudo chmod -R 755 /var/www/ids
```

### Session Storage
```bash
sudo mkdir -p /var/www/ids/flask_session
sudo chown www-data:www-data /var/www/ids/flask_session
```

Update `.env`:
```
SESSION_TYPE=filesystem
SESSION_FILE_DIR=/var/www/ids/flask_session
```

## Step 9: Logging Setup

### Application Logs
```bash
sudo mkdir -p /var/log/ids
sudo chown www-data:www-data /var/log/ids
```

### Configure Logging in config.py (optional)
Add to config.py:
```python
LOG_FILE = os.getenv('LOG_FILE', '/var/log/ids/app.log')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

## Step 10: Monitoring and Maintenance

### Check Service Status
```bash
sudo systemctl status ids
sudo journalctl -u ids -f
```

### View Logs
```bash
sudo tail -f /var/log/nginx/ids_access.log
sudo tail -f /var/log/nginx/ids_error.log
```

### Restart Services
```bash
sudo systemctl restart ids
sudo systemctl restart nginx
```

## Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u ids -n 50
```

### Permission Issues
```bash
sudo chown -R www-data:www-data /var/www/ids
sudo chmod -R 755 /var/www/ids
```

### Database Connection Issues
```bash
sudo -u postgres psql -U ids_user -d ids_db
```

### Port Already in Use
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

## Backup Strategy

### Database Backup
```bash
pg_dump -U ids_user ids_db > backup_$(date +%Y%m%d).sql
```

### Application Backup
```bash
tar -czf ids_backup_$(date +%Y%m%d).tar.gz /var/www/ids
```

## Performance Tuning

### Gunicorn Workers
Adjust workers in `/etc/systemd/system/ids.service`:
```
ExecStart=/var/www/ids/venv/bin/gunicorn --workers 4 --threads 2 --bind unix:ids.sock -m 007 wsgi:app
```

Rule of thumb: (2 x CPU cores) + 1 workers

### Nginx Caching
Add to nginx.conf for static files:
```
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| FLASK_ENV | Environment (production/development) | Yes |
| SECRET_KEY | Flask secret key | Yes |
| API_KEY | API authentication key | Yes |
| DATABASE_URL | PostgreSQL connection string | Yes |
| SESSION_TYPE | Session storage type | No |
| LOG_LEVEL | Logging level (DEBUG/INFO/ERROR) | No |

## Post-Deployment Checklist

- [ ] Application accessible via HTTPS
- [ ] SSL certificate valid and auto-renewal configured
- [ ] Database connection working
- [ ] User authentication functional
- [ ] Static files loading correctly
- [ ] API endpoints responding
- [ ] Logs being written
- [ ] Firewall configured
- [ ] Backup strategy in place
- [ ] Monitoring configured
