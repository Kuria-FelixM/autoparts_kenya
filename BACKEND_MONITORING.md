# Backend API Logging & Monitoring Guide

## 📊 Logging Overview

### Log Sources

1. **Django Application** - `/app/logs/django.log`
2. **Gunicorn Server** - Docker logs (stdout)
3. **Celery Worker** - Docker logs (stdout)
4. **PostgreSQL Database** - Docker logs (stdout)
5. **Redis** - Docker logs (stdout)
6. **Nginx** - `/var/log/nginx/autoparts_*.log`

---

## 🔍 Viewing Logs

### Using management script

```bash
cd /opt/autoparts/backend

# Backend API logs
./manage.sh logs web

# Celery worker logs
./manage.sh logs celery

# Database logs
./manage.sh logs db

# Redis logs
./manage.sh logs redis

# Last 50 lines
docker-compose -f docker-compose.prod.yml logs --tail=50 web

# Real-time follow
docker-compose -f docker-compose.prod.yml logs -f web

# Logs from last hour
docker-compose -f docker-compose.prod.yml logs --since 60m web
```

### Django Application Logs

```bash
# View Django application logs
docker-compose -f docker-compose.prod.yml exec web tail -f logs/django.log

# Search for errors
docker-compose -f docker-compose.prod.yml exec web grep ERROR logs/django.log

# Get last 20 errors
docker-compose -f docker-compose.prod.yml exec web grep ERROR logs/django.log | tail -20

# Search by date
docker-compose -f docker-compose.prod.yml exec web grep "2024-02-18" logs/django.log | head -50
```

---

## 📈 Monitoring

### System Health

```bash
# Full health check
./manage.sh health

# Output includes:
# - Backend API status
# - Database status
# - Redis status
# - Resource usage (memory, CPU)
```

### Container Resource Usage

```bash
# Real-time stats
docker stats

# Watch specific container
watch -n 1 docker stats autoparts_web_prod

# Export to file
docker stats --no-stream > /tmp/docker_stats.txt
```

### Database Performance

```bash
# Database connection status
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Database size
docker-compose -f docker-compose.prod.yml exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT pg_size_pretty(pg_database_size('autoparts_kenya_prod'));"

# Active connections
docker-compose -f docker-compose.prod.yml exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Slow queries (if enabled)
docker-compose -f docker-compose.prod.yml exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

### Redis Performance

```bash
# Connect to Redis CLI
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Inside redis-cli:
INFO              # Server statistics
DBSIZE            # Number of keys
KEYS *            # All keys
MONITOR           # Watch all commands
CLIENT LIST       # Connected clients
LASTSAVE          # Last save time
```

---

## 🔧 API Health Monitoring

### Health Check Endpoint

```bash
# Test API health
curl https://your_domain.com/api/v1/health/

# Expected response:
# HTTP 200 with status "healthy"
```

### API Response Monitoring

```bash
# Check API response time
curl -w "Time: %{time_total}s\n" https://your_domain.com/api/v1/health/

# Monitor with watch
watch -n 5 "curl -w 'Time: %{time_total}s\n' https://your_domain.com/api/v1/health/"
```

### Request/Response Logging

Add to Django settings for detailed logging:

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

---

## 📊 Nginx Monitoring

### Access Logs

```bash
# View access logs
tail -f /var/log/nginx/autoparts_access.log

# Count requests per minute
tail -100 /var/log/nginx/autoparts_access.log | awk '{print $4}' | cut -d: -f1-3 | sort | uniq -c

# Find 5xx errors
grep ' 5[0-9][0-9] ' /var/log/nginx/autoparts_access.log | tail -20

# Find 4xx errors
grep ' 4[0-9][0-9] ' /var/log/nginx/autoparts_access.log | tail -20
```

### Error Logs

```bash
# View error logs
tail -f /var/log/nginx/autoparts_error.log

# Find specific errors
grep "upstream timed out" /var/log/nginx/autoparts_error.log
grep "connection refused" /var/log/nginx/autoparts_error.log
```

### Performance Analysis

```bash
# Average response time (from logs)
tail -100 /var/log/nginx/autoparts_access.log | \
  awk '{print $NF}' | \
  awk '{sum+=$1} END {print sum/NR}'

# Requests per second
tail -100 /var/log/nginx/autoparts_access.log | wc -l

# Bandwidth usage
tail -100 /var/log/nginx/autoparts_access.log | \
  awk '{sum+=$10} END {print sum/1024/1024 " MB"}'
```

---

## 🐛 Debugging Issues

### Backend API Not Responding

```bash
# 1. Check if service is running
./manage.sh status

# 2. Check logs for errors
./manage.sh logs web

# 3. Test connection locally
docker-compose -f docker-compose.prod.yml exec web curl http://localhost:8000/api/v1/health/

# 4. Check if port is open
netstat -tulpn | grep 8000

# 5. Check Nginx is forwarding correctly
curl -v http://127.0.0.1:8000/api/v1/health/
```

### Database Connection Errors

```bash
# 1. Check database is running
./manage.sh logs db

# 2. Test database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell

# 3. Check credentials
cat .env | grep DB_

# 4. Verify network connectivity
docker-compose -f docker-compose.prod.yml exec web ping db

# 5. Check database logs for errors
docker-compose -f docker-compose.prod.yml logs db | grep ERROR
```

### High Memory Usage

```bash
# 1. Check current usage
docker stats autoparts_web_prod

# 2. Check Python processes
docker-compose -f docker-compose.prod.yml exec web ps aux

# 3. Monitor memory trends
watch -n 5 "docker stats --no-stream autoparts_web_prod"

# 4. Check for memory leaks in logs
./manage.sh logs web | grep -i memory
```

### Slow API Responses

```bash
# 1. Check database query performance
docker-compose -f docker-compose.prod.yml logs web | grep "seconds"

# 2. Check if database is bottleneck
docker-compose -f docker-compose.prod.yml exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT * FROM pg_stat_activity ORDER BY query_start DESC LIMIT 5;"

# 3. Check Redis performance
docker-compose -f docker-compose.prod.yml exec redis redis-cli --latency

# 4. Check Nginx response times
tail -50 /var/log/nginx/autoparts_access.log | awk '{print $NF}' | sort -nr | head -10
```

---

## 📋 Monitoring Checklist

### Daily (5 min)
```bash
./manage.sh health          # Overall status
./manage.sh logs web        # Check for errors
tail -20 /var/log/nginx/autoparts_error.log
```

### Weekly (30 min)
```bash
# Database health
docker-compose exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "VACUUM ANALYZE"

# Check backups
ls -lh backups/ | head -10

# Review error patterns
./manage.sh logs web | grep ERROR | head -20

# Resource trends
docker stats --no-stream
```

### Monthly (1 hour)
```bash
# Database size
docker-compose exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT pg_size_pretty(pg_database_size('autoparts_kenya_prod'));"

# Query performance
docker-compose exec db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 20;"

# Cleanup old logs
find logs -name "*.log" -mtime +30 -delete

# Test backups
./manage.sh restore backups/[latest_backup].sql.gz  # Test only in test environment
```

---

## 📊 Setting Up Monitoring Dashboard (Optional)

### With Prometheus & Grafana

```bash
# Install Prometheus exporter for Docker
pip install prometheus-client

# Add to Django settings
MIDDLEWARE += ['prometheus_client.middleware.PrometheusMiddleware']

# Configure Grafana dashboard:
http://localhost:3000
# Add Prometheus data source
# Create custom dashboard for API metrics
```

---

## 🔔 Alert Setup

### Custom Alert Script

Create `scripts/alert.sh`:

```bash
#!/bin/bash

# Check if API is responding
if ! curl -sf http://localhost:8000/api/v1/health/ > /dev/null; then
    echo "ALERT: API is down!" | mail -s "AutoParts Backend Down" admin@autoparts.ke
    exit 1
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "ALERT: Disk usage at ${DISK_USAGE}%" | mail -s "Disk Usage Alert" admin@autoparts.ke
fi

# Check database size
DB_SIZE=$(docker-compose exec -T db psql -U autoparts_prod_user autoparts_kenya_prod \
  -c "SELECT pg_size_pretty(pg_database_size('autoparts_kenya_prod'));" | tail -1)
echo "Database size: $DB_SIZE"

exit 0
```

Add to crontab:
```bash
# Run every 5 minutes
*/5 * * * * /opt/autoparts/backend/scripts/alert.sh
```

---

## 📚 Log Retention

### Setup Log Rotation

```bash
sudo tee /etc/logrotate.d/autoparts << EOF
/opt/autoparts/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
}

/var/log/nginx/autoparts*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        nginx -s reload > /dev/null 2>&1 || true
    endscript
}
EOF

# Test rotation
sudo logrotate -d /etc/logrotate.d/autoparts
```

---

## 🎯 Performance Benchmarks

Expected performance metrics:

| Metric | Target | Alert |
|--------|--------|-------|
| API Response Time | <200ms | >500ms |
| Database Response | <50ms | >100ms |
| Memory Usage | <1GB | >2GB |
| CPU Usage | <50% | >80% |
| Disk Usage | <70% | >85% |
| Celery Queue | <1000 | >5000 |

---

## 📞 Quick Commands Reference

```bash
# Status & Health
./manage.sh health
./manage.sh status

# Logs
./manage.sh logs web
./manage.sh logs celery
./manage.sh logs db

# Database
docker-compose exec db psql -U autoparts_prod_user autoparts_kenya_prod

# Redis
docker-compose exec redis redis-cli

# Backups
./manage.sh backup
./manage.sh restore FILE

# Resources
docker stats
du -sh /opt/autoparts/backend
df -h
```

---

**Version**: 1.0.0  
**Last Updated**: February 18, 2024  
**Status**: Production Ready ✅
