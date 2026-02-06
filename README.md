# AutoParts Kenya - Backend API

Professional Django REST Framework e-commerce API for automotive spare parts in Kenya. Single-owner store with guest checkout, M-Pesa integration, and comprehensive admin analytics.

## 📋 Project Structure

```
autoparts_kenya/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── autoparts_kenya/              # Main project config
│   ├── __init__.py
│   ├── settings.py              # Full Django + DRF + Celery config
│   ├── urls.py                  # Root URL routes + Swagger
│   ├── asgi.py
│   ├── wsgi.py
│   └── celery.py                # Celery + Redis config
│
├── core/                         # Shared utilities
│   ├── permissions.py           # IsOwner, IsOwnerOrReadOnly, IsAuthenticatedOrReadOnly
│   └── utils.py                 # Delivery calc, M-Pesa validation, currency formatting
│
├── users/                        # User auth & profiles
│   ├── models.py                # User, UserProfile (is_owner flag), SavedVehicle, SavedAddress
│   ├── serializers.py           # Registration, Profile, Saved items
│   ├── views.py                 # Registration, Profile, SavedVehicles, SavedAddresses ViewSets
│   └── urls.py
│
├── vehicles/                     # Vehicle makes/models (compatibility backbone)
│   ├── models.py                # VehicleMake, VehicleModel
│   ├── serializers.py
│   ├── views.py                 # Public GET, Owner-only write
│   └── urls.py
│
├── products/                     # Product catalog
│   ├── models.py                # Category, Product, ProductImage (ManyToMany to VehicleModel)
│   ├── serializers.py           # Category + Product (list/detail/create)
│   ├── views.py                 # Advanced filtering: vehicle, price, category, inventory
│   ├── tasks.py                 # Celery: check_low_stock
│   └── urls.py
│
├── orders/                       # Checkout & order management
│   ├── models.py                # Order (guest + auth), OrderItem, status tracking
│   ├── serializers.py           # Checkout, OrderList, OrderDetail
│   ├── views.py                 # Checkout (guest/auth), OrderHistory, OwnerManagement
│   └── urls.py
│
├── payments/                     # M-Pesa integration
│   ├── models.py                # TransactionLog
│   ├── utils.py                 # DarajaAPI wrapper (STK Push, callback handling)
│   ├── serializers.py
│   ├── views.py                 # STK Push initiation, M-Pesa callback webhook
│   ├── tasks.py                 # Celery: async callback processing
│   └── urls.py
│
├── analytics/                    # Owner-only dashboards
│   ├── views.py                 # Dashboard, Revenue, Top products, Low stock, Profit
│   └── urls.py
│
├── media/                        # Product images
│   └── products/
│
└── logs/                         # Application logs
```

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- virtualenv

### 2. Setup

```bash
# Clone repo
cd autoparts_kenya

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your database, M-Pesa credentials, etc.

# Create database
python manage.py migrate

# Create superuser (store owner)
python manage.py createsuperuser

# Create initial data (vehicle makes/models)
python manage.py loaddata vehicles_initial_data.json  # (create this fixture)

# Run development server
python manage.py runserver

# In another terminal, run Celery worker
celery -A autoparts_kenya worker -l info

# In another terminal, run Celery Beat (scheduled tasks)
celery -A autoparts_kenya beat -l info
```

### 3. Access API
- **API Root**: http://localhost:8000/api/v1/
- **Swagger Docs**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin**: http://localhost:8000/admin/

## 🔐 Authentication

- **Public Endpoints**: GET endpoints (products, vehicles, categories) → no auth required (guest-first)
- **Protected Endpoints**: POST/PUT/DELETE → JWT Bearer token
- **Owner-Only**: Admin endpoints (products CRUD, orders management, analytics) → requires `is_owner=True`

### Token Endpoints
```bash
# Get tokens
POST /api/v1/users/token/
{
  "username": "your_username",
  "password": "your_password"
}

# Refresh token
POST /api/v1/users/token/refresh/
{
  "refresh": "your_refresh_token"
}
```

## 📦 Main Features

### 1. **Guest Checkout** (No Registration)
```bash
POST /api/v1/orders/checkout/
{
  "items": [{"product_id": 1, "quantity": 2}],
  "delivery_address": "123 Kenyatta Ave, Nairobi",
  "recipient_name": "John Doe",
  "recipient_phone": "+254712345678",
  "guest_email": "john@example.com"
}
```

### 2. **M-Pesa Payment** (Daraja API - STK Push)
```bash
POST /api/v1/payments/initiate-stk-push/
{
  "order_id": 1,
  "phone_number": "+254712345678"
}
# Webhook: /api/v1/payments/mpesa-callback/
```

### 3. **Vehicle Compatibility Filtering**
```bash
GET /api/v1/products/products/?vehicle_make=1&vehicle_year=2020
GET /api/v1/products/products/?vehicle_model=5
```

### 4. **Admin Dashboard** (Owner-only)
```bash
GET /api/v1/analytics/dashboard/
GET /api/v1/analytics/revenue/
GET /api/v1/analytics/top-products/?limit=10
GET /api/v1/analytics/low-stock/?threshold=10
GET /api/v1/analytics/profit/
GET /api/v1/orders/admin/orders/
```

### 5. **Saved Vehicles & Addresses** (Authenticated)
```bash
GET/POST /api/v1/users/saved-vehicles/
GET/POST /api/v1/users/saved-addresses/
```

## 📊 Key Models & Relationships

- **User** ↔ **UserProfile** (one-to-one, is_owner flag)
- **Product** ↔ **VehicleModel** (many-to-many, compatibility)
- **Order** ↔ **OrderItem** ↔ **Product**
- **Order** → **TransactionLog** (payment tracking)
- **User** → **SavedVehicle**, **SavedAddress** (personalization)

## 🛠️ Database Indexes & Optimization

All critical filter fields are indexed:
- `products_product.sku`, `products_product.category`, `products_product.stock`
- `vehicles_model.year_from`, `vehicles_model.year_to`
- `orders_order.order_number`, `orders_order.user`, `orders_order.payment_status`
- `payments_transaction_log.checkout_request_id`

Pagination: 20 items per page (configurable in settings)

## 🔄 Celery Tasks

- `products.tasks.check_low_stock()` - Hourly inventory alert
- `payments.tasks.process_mpesa_callback()` - Async payment confirmation

## 📝 API Documentation

All endpoints documented with:
- **@extend_schema** decorators
- **OpenAPI examples**
- **Parameter descriptions**
- **Error codes**

Access Swagger: http://localhost:8000/api/docs/

## 🇰🇪 Kenyan Localization

- **Currency**: KSh (Kenyan Shillings)
- **Timezone**: Africa/Nairobi
- **Delivery Base**: Nairobi (2-3 days standard)
- **Phone Format**: +254XXXXXXX or 0XXXXXXX → 254XXXXXXX
- **Swahili Tooltips**: Error messages include Swahili translations
- **M-Pesa**: Full Daraja API integration (sandbox & production modes)

## 🔐 Security Features

- CORS whitelisting
- CSRF protection
- JWT Bearer auth
- SQL injection prevention (ORM + parameterized queries)
- Rate throttling: 100/hour (anon), 1000/hour (user)
- HTTPS required in production
- XSS protection

## 📧 Optional Enhancements

- Email notifications (order confirmation, low stock)
- SMS via Africastalking API
- AWS S3 for product images
- Sentry for error tracking
- Analytics with Mixpanel/Segment

## 🚢 Deployment

### Docker Compose
Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: autoparts_kenya
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  redis:
    image: redis:7-alpine
  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      DEBUG: 'False'
      ALLOWED_HOSTS: 'api.autoparts.ke'
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  celery:
    build: .
    command: celery -A autoparts_kenya worker -l info
    depends_on:
      - db
      - redis
```

### Environment Variables (Production)
```bash
SECRET_KEY=your-production-secret
DEBUG=False
ALLOWED_HOSTS=api.autoparts.ke
DB_ENGINE=django.db.backends.postgresql
DB_NAME=autoparts_kenya_prod
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_HOST=rds.amazonaws.com
CELERY_BROKER_URL=redis://elasticache-url:6379/0
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY=prod_key
MPESA_CONSUMER_SECRET=prod_secret
```

## 📞 Support

**API Issues**: Check logs in `logs/autoparts.log`
**M-Pesa Issues**: Review `TransactionLog` model in admin
**Performance**: Use Django Debug Toolbar in dev, check slow queries

## 📄 License

Proprietary - AutoParts Kenya

---

**Last Updated**: February 6, 2025  
**Django Version**: 5.1+  
**Python Version**: 3.10+
