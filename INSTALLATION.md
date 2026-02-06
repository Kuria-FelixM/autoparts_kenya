# AutoParts Kenya - Installation & Setup Guide

## Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- pip & virtualenv
- Git

## Local Development Setup

### Step 1: Clone Repository & Navigate
```bash
cd /path/to/autoparts_kenya
pwd  # Verify you're in project root
```

### Step 2: Create Virtual Environment
```bash
# Create venv
python3 -m venv venv

# Activate
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify activation (you should see (venv) in terminal)
```

### Step 3: Upgrade pip & Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Database Setup

#### Option A: PostgreSQL (Recommended)
```bash
# Create database
createdb autoparts_kenya
# Or if createdb not in PATH, use psql:
psql -U postgres -c "CREATE DATABASE autoparts_kenya;"

# Test connection
psql -U postgres -d autoparts_kenya -c "\dt"
```

#### Option B: SQLite (Quick Testing)
Change DB in settings.py:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### Step 5: Environment Configuration
```bash
# Copy example env
cp .env.example .env

# Edit .env with your settings
nano .env  # or open in editor
```

**Critical .env variables:**
```env
SECRET_KEY=generate-secure-key  # Run: python -c 'import secrets; print(secrets.token_urlsafe(50))'
DEBUG=True                        # False in production
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=autoparts_kenya
DB_USER=postgres
DB_PASSWORD=YOUR_PASSWORD
DB_HOST=localhost
DB_PORT=5432

# Redis (Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# M-Pesa (Use sandbox credentials for testing)
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=your_sandbox_key
MPESA_CONSUMER_SECRET=your_sandbox_secret
MPESA_BUSINESS_SHORTCODE=174379  # Test shortcode
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd1a503b6015d86d3b50c3cc1f  # Test passkey
```

### Step 6: Run Migrations
```bash
python manage.py migrate
```

Expected output:
```
Applying contenttypes.0001_initial... OK
Applying auth.0001_initial... OK
...
Applying payments.0001_initial... OK
Running migrations:
  No migrations to apply.
```

### Step 7: Create Superuser (Store Owner)
```bash
python manage.py createsuperuser
```

Follow prompts:
```
Username: owner
Email: owner@autoparts.ke
Password: [secure password]
Password (again): [confirm]
Superuser created successfully.
```

**After creation, mark as owner:**
```bash
python manage.py shell
```

```python
from users.models import UserProfile
from django.contrib.auth.models import User

user = User.objects.get(username='owner')
profile, created = UserProfile.objects.get_or_create(user=user)
profile.is_owner = True
profile.save()
print(f"Owner status set: {profile.is_owner}")
exit()
```

### Step 8: Create Sample Data (Optional)

You can use Django admin to add vehicle makes/models and categories manually:

```bash
python manage.py runserver
# Visit http://localhost:8000/admin
# Login with your superuser credentials
# Add:
# - VehicleMakes (Toyota, Nissan, etc.)
# - VehicleModels (Corolla, Altima, etc.)
# - Categories (Engine Parts, Brake Systems, etc.)
# - Products
```

### Step 9: Run Development Server
```bash
python manage.py runserver
```

Output:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

Access:
- **API Root**: http://localhost:8000/api/v1/
- **Swagger Docs**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

### Step 10: Run Celery Worker (In separate terminal)

```bash
# Activate venv if not already active
source venv/bin/activate

# Run Celery worker
celery -A autoparts_kenya worker -l info
```

Output:
```
 -------------- celery@hostname v5.3.4 (emerald-rush)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ---------- .
- ** ---------- Concurrency: 4 (prefork)
- ** ---------- [queues]
 -------------- .

[2025-02-06 14:45:30,123: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-02-06 14:45:30,456: INFO/MainProcess] ready.
```

### Step 11: Run Celery Beat (In another terminal for scheduled tasks)

```bash
# Activate venv if not already active
source venv/bin/activate

# Run Celery Beat
celery -A autoparts_kenya beat -l info
```

---

## Testing the API

### Test 1: List Products (Public)
```bash
curl http://localhost:8000/api/v1/products/products/ \
  -H "Accept: application/json" | python -m json.tool
```

### Test 2: Register User
```bash
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "password_confirm": "TestPass123"
  }' | python -m json.tool
```

### Test 3: Get Token
```bash
curl -X POST http://localhost:8000/api/v1/users/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123"
  }' | python -m json.tool
```

### Test 4: Guest Checkout
```bash
curl -X POST http://localhost:8000/api/v1/orders/checkout/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{"product_id": 1, "quantity": 1}],
    "delivery_address": "123 Test Street",
    "recipient_name": "John Doe",
    "recipient_phone": "+254712345678",
    "guest_email": "guest@example.com"
  }' | python -m json.tool
```

### Test 5: Access Analytics (Owner only)
```bash
curl http://localhost:8000/api/v1/analytics/dashboard/ \
  -H "Authorization: Bearer <your_token>"
```

---

## Troubleshooting

### Issue: `django.db.utils.OperationalError: connection refused`
**Solution**: Make sure PostgreSQL is running
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Or start it
sudo systemctl start postgresql
```

### Issue: `ConnectionError: Error 111 connecting to localhost:6379`
**Solution**: Make sure Redis is running
```bash
# Start Redis
redis-server

# Or in background
redis-server &
```

### Issue: `ModuleNotFoundError: No module named 'rest_framework'`
**Solution**: Ensure venv is activated and requirements installed
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Migrations fail
**Solution**: Reset and re-run migrations
```bash
# Delete all migrations (except __init__.py) and db
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

### Issue: Celery not processing tasks
**Solution**: Ensure Redis is working and Celery worker is running
```bash
# Test Redis
redis-cli ping
# Should return: PONG

# Check Celery worker is running in separate terminal
celery -A autoparts_kenya worker -l info
```

---

## Next Steps

1. **Read API Endpoints**: See [API_ENDPOINTS.md](API_ENDPOINTS.md)
2. **Test with Swagger**: Go to http://localhost:8000/api/docs/
3. **Set up Frontend**: Connect mobile/web frontend to API
4. **Configure M-Pesa**: Get real Daraja API credentials from Safaricom
5. **Deploy**: Follow deployment guide for production setup

---

## Quick Commands Reference

```bash
# Development
python manage.py runserver
celery -A autoparts_kenya worker -l info
celery -A autoparts_kenya beat -l info

# Migrations
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Database
python manage.py shell
python manage.py dbshell

# Admin
python manage.py createsuperuser
python manage.py changepassword <username>

# Testing
python manage.py test
pytest

# Static files
python manage.py collectstatic
```

---

**Last Updated**: February 6, 2025
