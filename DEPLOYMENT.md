# Backend-Only Production Deployment Guide

## 📊 Quick Overview

This guide is for deploying **backend only** on a Digital Ocean Droplet:
- ✅ Django REST API (backend)
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ Celery Workers
- ❌ Frontend (deployed separately on different server/CDN)

---

## 📋 Pre-Deployment Checklist

- [ ] Digital Ocean Droplet (2GB+ RAM, Ubuntu 22.04 LTS)
- [ ] Domain name pointing to droplet (e.g., `api.autoparts.ke`)
- [ ] SSH access configured
- [ ] M-Pesa production credentials
- [ ] Backend repository cloned

---

## 🚀 Quick Deployment (25 minutes)

### Step 1: SSH into Droplet (1 min)

```bash
ssh root@your_droplet_ip

# Update system
apt-get update && apt-get upgrade -y
timedatectl set-timezone Africa/Nairobi
```

### Step 2: Install Docker (5 min)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify
docker --version
```

### Step 3: Clone Backend Repository (2 min)

```bash
cd /opt/autoparts
git clone https://github.com/yourusername/autoparts_kenya.git backend
cd backend
```

### Step 4: Configure Environment (3 min)

```bash
# Copy environment template
cp docker/.env.production .env

# Generate secure credentials (no Django needed!)
DJANGO_SECRET=$(openssl rand -base64 64)
DB_PASSWORD=$(openssl rand -base64 32)
REDIS_PASSWORD=$(openssl rand -base64 32)

# Update .env with generated values
sed -i "s/SECRET_KEY=.*/SECRET_KEY=$DJANGO_SECRET/" .env
sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=$DB_PASSWORD/" .env
sed -i "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=$REDIS_PASSWORD/" .env

# Verify values were set
echo "✅ Secrets generated:"
grep -E "SECRET_KEY|DB_PASSWORD|REDIS_PASSWORD" .env | head -3

# Now edit remaining values manually
nano .env
# Update:
# - ALLOWED_HOSTS=your_droplet_ip  (or your_domain.com when ready)
# - CORS_ALLOWED_ORIGINS=*         (adjust before going live)
# - MPESA keys (production)
```

### Step 5: Setup SSL Certificate (3 min)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot certonly --standalone -d your_domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Step 6: Configure Nginx (3 min)

```bash
# Copy nginx config
sudo cp docker/nginx.conf.prod /etc/nginx/sites-available/autoparts.conf

# Update domain name
sudo sed -i 's/your_domain.com/your_actual_domain.com/g' /etc/nginx/sites-available/autoparts.conf

# Enable site
sudo ln -s /etc/nginx/sites-available/autoparts.conf /etc/nginx/sites-enabled/

# Test & restart
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Start Backend Services (5 min)

```bash
cd /opt/autoparts/backend

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Initialize database
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

health# Verify
docker-compose -f docker-compose.prod.yml ps
./manage.sh 
```

✅ **Backend is now running!** Test with:

```bash
curl https://your_domain.com/api/v1/health/
```

---

## 📁 File Structure

```
/opt/autoparts/backend/
├── docker-compose.prod.yml    # Production Docker setup
├── docker/
│   ├── nginx.conf.prod        # Nginx reverse proxy
│   └── .env.production        # Environment template
├── manage.sh                  # Management script
├── .env                       # Production secrets (not in git)
├── Dockerfile                 # Backend image
├── requirements.txt           # Python dependencies
├── manage.py
├── autoparts_kenya/           # Django project
│   ├── settings.py
│   ├── urls.py
│   └── ...
└── [apps...]
```

---

## 🛠️ Daily Operations

### Start/Stop Services

```bash
cd /opt/autoparts/backend

# Start
./manage.sh start

# Stop
./manage.sh stop

# Status
./manage.sh status
```

### View Logs

```bash
# Backend API logs
./manage.sh logs web

# Celery worker logs
./manage.sh logs celery

# Database logs
./manage.sh logs db

# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f web
```

### Backup Database

```bash
# Create backup
./manage.sh backup

# This creates: backups/autoparts_backup_20240218_120000.sql.gz

# Restore (if needed)
./manage.sh restore ./backups/autoparts_backup_20240218_120000.sql.gz
```

### Health Check

```bash
./manage.sh health

# Output:
# Backend API: Running
# Database: Running
# Redis: Running
# [Resource Usage stats]
```

---

## 🐞 Troubleshooting

### Services Won't Start

```bash
# Check logs
./manage.sh logs web

# Common issues:
docker-compose ps db         # Is database running?
docker-compose logs db       # Database errors?

# Rebuild if needed
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d
```

### CORS Errors (Frontend Can't Connect)

```bash
# Check CORS settings in .env
grep CORS_ALLOWED_ORIGINS .env

# Must include your frontend domain:
# CORS_ALLOWED_ORIGINS=https://your_frontend_domain.com

# Test endpoint
curl -i https://your_domain.com/api/v1/health/

# Should include:
# access-control-allow-origin: https://your_frontend_domain.com
```

### Database Connection Issues

```bash
# Check if database is healthy
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Check credentials in .env
cat .env | grep DB_

# Restart database
docker-compose -f docker-compose.prod.yml restart db
```

---

## 📊 Monitoring

### Daily Checks

```bash
# Run health check
./manage.sh health

# Check disk space
df -h

# Check logs for errors
./manage.sh logs web | grep ERROR
```

### Weekly Tasks

```bash
# Backup database
./manage.sh backup

# Check resource usage
docker stats

# Review error logs
tail -100 /var/log/nginx/autoparts_error.log
```

### Monthly Tasks

```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Optimize database
docker-compose exec db vacuum analyze

# Check certificate validity
sudo certbot certificates
```

---

## 📈 Scaling

### Add More Celery Workers

```yaml
# docker-compose.prod.yml
celery:
  command: celery -A autoparts_kenya worker -l info --concurrency=8
```

### Increase Gunicorn Workers

```yaml
# docker-compose.prod.yml
web:
  command: >
    sh -c "
      python manage.py migrate &&
      gunicorn autoparts_kenya.wsgi:application 
        --workers 8  # Increase from 4
```

### Database Optimization

```bash
# Enable slow query log
docker-compose exec db psql -U autoparts_prod_user -d autoparts_kenya_prod -c \
  "ALTER SYSTEM SET log_min_duration_statement = 1000;"

# Restart database
docker-compose restart db
```

---

## 🔐 Security

✅ **Already Configured**:
- HTTPS with Let's Encrypt
- HSTS headers
- CSRF protection
- SQL injection prevention
- Non-root containers

✅ **Recommended Additional**:
- Enable firewall (ufw)
- SSH key-based auth only
- Fail2ban for brute force
- Database backups to cloud storage
- Regular updates

```bash
# Enable UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

---

## 🆘 Support

| Issue | Solution |
|-------|----------|
| Services won't start | Check `./manage.sh logs web` |
| CORS errors | Update `CORS_ALLOWED_ORIGINS` in `.env` |
| Database errors | Run `./manage.sh logs db` |
| High CPU usage | Check `docker stats` and worker count |
| Disk full | Run `docker system prune -a` |

---

## 📚 Next Steps

1. **Monitor in production**: Run `./manage.sh health` daily
2. **Setup backups**: Add cron job for `./manage.sh backup`
3. **Configure email**: Setup SMTP for notifications
4. **Analytics**: Connect to monitoring service
5. **Frontend**: Deploy frontend on separate server/CDN

---

## 📝 Useful Commands

```bash
# Show all commands
./manage.sh help

# Execute Django command
docker-compose -f docker-compose.prod.yml exec web python manage.py [command]

# Create admin user
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Database shell
docker-compose -f docker-compose.prod.yml exec db psql -U autoparts_prod_user autoparts_kenya_prod

# Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# View live logs
tail -f /var/log/nginx/autoparts_access.log
```

---

**Version**: 1.0.0  
**Last Updated**: February 18, 2024  
**Status**: Production Ready ✅
