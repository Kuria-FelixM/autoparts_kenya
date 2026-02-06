# Project Structure Summary

Complete Django REST Framework e-commerce API for AutoParts Kenya.

## 📁 Project Layout

```
autoparts_kenya/
│
├── 📄 manage.py                    # Django management script
├── 📄 requirements.txt             # Python dependencies
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore rules
│
├── 🔧 autoparts_kenya/             # Main project configuration
│   ├── __init__.py
│   ├── settings.py                 # Full Django + DRF config
│   ├── urls.py                     # Root URL routing + Swagger
│   ├── asgi.py                     # ASGI server config
│   ├── wsgi.py                     # WSGI server config
│   └── celery.py                   # Celery + Redis config
│
├── 🔐 core/                        # Shared utilities & permissions
│   ├── __init__.py
│   ├── permissions.py              # IsOwner, IsOwnerOrReadOnly, IsAuthenticatedOrReadOnly
│   └── utils.py                    # Delivery calc, M-Pesa phone validation, KSh formatting
│
├── 👤 users/                       # User authentication & profiles
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # User, UserProfile, SavedVehicle, SavedAddress
│   ├── serializers.py              # Registration, Profile, Vehicles, Addresses
│   ├── views.py                    # Registration, Profile, Vehicles, Addresses ViewSets
│   └── urls.py                     # User routes
│
├── 🚗 vehicles/                    # Vehicle compatibility system
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # VehicleMake, VehicleModel
│   ├── serializers.py              # Make & Model serializers
│   ├── views.py                    # Make & Model ViewSets (public read, owner write)
│   └── urls.py                     # Vehicle routes
│
├── 📦 products/                    # Product catalog
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # Category, Product, ProductImage, ManyToMany to Vehicles
│   ├── serializers.py              # Category, Product (list/detail/create)
│   ├── views.py                    # Category & Product ViewSets with advanced filtering
│   ├── tasks.py                    # Celery: check_low_stock()
│   └── urls.py                     # Product routes
│
├── 🛒 orders/                      # Checkout & order management
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # Order (guest + auth), OrderItem, status tracking
│   ├── serializers.py              # Checkout, OrderList, OrderDetail
│   ├── views.py                    # Checkout (guest/auth), OrderHistory, Admin management
│   └── urls.py                     # Order routes
│
├── 💳 payments/                    # M-Pesa / Daraja API integration
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                   # TransactionLog for audit
│   ├── utils.py                    # DarajaAPI wrapper for STK Push
│   ├── serializers.py              # STK Push & Callback serializers
│   ├── views.py                    # STK Push initiation, M-Pesa webhook
│   ├── tasks.py                    # Celery: process_mpesa_callback()
│   └── urls.py                     # Payment routes
│
├── 📊 analytics/                   # Owner-only business metrics
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py                    # Dashboard, Revenue, Top products, Profit analysis
│   └── urls.py                     # Analytics routes
│
├── 📸 media/                       # User uploads
│   └── products/                   # Product images
│
├── 📝 logs/                        # Application logs
│   └── autoparts.log
│
├── 📋 README.md                    # Project overview
├── 📚 INSTALLATION.md              # Setup guide
├── 🔌 API_ENDPOINTS.md             # Complete API reference
└── 📖 PROJECT_STRUCTURE.md         # This file
```

## 🎯 Key Features by Module

### Core Module
- **Permissions**: Custom permission classes for guest-first design
- **Utilities**: Delivery time calculation, M-Pesa phone validation, currency formatting

### Users Module
- JWT-based authentication (simplejwt)
- User registration endpoint (guests → registered users)
- UserProfile with owner identification
- Saved vehicles for quick product filtering
- Saved addresses for faster checkout

### Vehicles Module
- VehicleMake model (manufacturers: Toyota, Nissan, etc.)
- VehicleModel with year ranges for compatibility
- Public read access, owner-only create/edit/delete
- Backbone for product compatibility system

### Products Module
- Category model with optional subcategories
- Product model with:
  - ManyToMany relationship to VehicleModel (compatibility)
  - Pricing with discount support
  - Inventory management (stock, reserved_stock)
  - Rating & review count
- Advanced filtering: vehicle, price range, category, in stock
- Featured products endpoint
- Celery task for low stock alerts

### Orders Module
- Guest checkout (no authentication required)
- Authenticated checkout with order history
- Order model with dual user/guest support
- OrderItem model with product snapshots (price at time of order)
- Order status tracking: pending → confirmed → processing → shipped → delivered
- Payment status tracking: unpaid → pending → paid → failed
- Admin order management interface

### Payments Module
- M-Pesa Daraja API integration
- STK Push initiation endpoint
- M-Pesa callback webhook (async via Celery)
- Transaction logging for audit trail
- Payment status checking
- Support for sandbox & production modes

### Analytics Module
- Dashboard: total revenue, orders, products, low stock count
- Revenue metrics: by day/week/month, average order value
- Top products: by quantity sold and revenue
- Low stock alert with configurable threshold
- Order status distribution
- Payment status distribution
- Profit margin analysis (cost_price-based)
- Owner-only access with drf-spectacular documentation

## 🔑 Key Concepts

### Guest-First Philosophy
Most GET endpoints allow unauthenticated access:
- Browse products
- Search by vehicle
- Guest checkout
- View public order details

Authentication (JWT) required for:
- Creating orders (authenticated user has order history)
- Saving vehicles/addresses
- Viewing personal order history
- All owner/admin actions

### Permission Hierarchy
1. **AllowAny**: Product list, vehicle details, guest checkout
2. **IsAuthenticatedOrReadOnly**: Profile, saved items
3. **IsOwner**: Admin endpoints (products CRUD, orders management, analytics)
4. **IsOwnerOrReadOnly**: Vehicle/Category management (public read, owner write)

### M-Pesa Integration
- STK Push: Prompt customer to enter M-Pesa PIN
- Callback: M-Pesa → webhook → Celery task → Order status update
- Transaction Log: Full audit trail of all payment attempts
- Support: Sandbox (testing) & Production modes

### Vehicle Compatibility
- Products linked to VehicleModel via ManyToMany
- Filtering: Find products by Make/Model/Year
- Year compatibility: Product works with a year if `year_from <= year <= year_to`

### Inventory Management
- Stock: Total units available
- Reserved stock: Units in pending orders
- Available stock: stock - reserved_stock
- Low stock alerts: Hourly Celery task

## 📊 Database Models

```
User
  ├─ UserProfile (is_owner flag)
  ├─ SavedVehicle
  ├─ SavedAddress
  └─ Order
     └─ OrderItem
        └─ Product

VehicleMake
  └─ VehicleModel
     ├─ Product (ManyToMany)
     └─ SavedVehicle

Category
  ├─ Category (parent/children)
  └─ Product
     ├─ ProductImage
     ├─ OrderItem
     └─ VehicleModel (ManyToMany)

Order
  ├─ OrderItem
  └─ TransactionLog

TransactionLog
  └─ Order
```

## 🔄 Request Flow Examples

### Guest Checkout → Payment
1. GET /api/v1/products/ → Browse products
2. POST /api/v1/orders/checkout/ → Create order (guest_email)
3. POST /api/v1/payments/initiate-stk-push/ → Start M-Pesa STK
4. Customer enters PIN on phone
5. M-Pesa sends callback to webhook
6. Celery task updates order.payment_status = 'paid'
7. Order confirmed

### Register → Order History
1. POST /api/v1/users/register/ → Create user account
2. POST /api/v1/users/token/ → Get JWT token
3. POST /api/v1/orders/checkout/ → Create authenticated order
4. GET /api/v1/orders/my-orders/ → View order history

### Owner Dashboard
1. GET /api/v1/analytics/dashboard/ → Key metrics
2. GET /api/v1/analytics/revenue/ → Revenue by period
3. GET /api/v1/analytics/top-products/ → Best sellers
4. GET /api/v1/analytics/profit/ → Profit analysis
5. GET /api/v1/orders/admin/orders/ → Manage all orders

## ⚡ Performance Optimizations

- **Database Indexes** on all filter fields (SKU, category, year, stock, payment_status)
- **select_related() & prefetch_related()** in ViewSets for eager loading
- **Pagination**: 20 items per page (configurable)
- **Lazy querysets**: Filters applied at database level
- **Celery**: Async M-Pesa callback processing (non-blocking)
- **Redis**: Caching & task queue

## 🔐 Security Features

- CORS whitelist (configurable origins)
- CSRF protection
- JWT Bearer authentication with rotating refresh tokens
- SQL injection prevention (ORM + parameterized queries)
- XSS protection (DRF JSON responses)
- Rate limiting: 100/hour (anon), 1000/hour (user)
- HTTPS enforced in production
- Secure password validation

## 📚 Documentation

All endpoints documented with:
- `@extend_schema` decorators
- OpenAPI examples
- Parameter descriptions
- Error codes & messages

Access at:
- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Schema: http://localhost:8000/api/schema/

## 🇰🇪 Kenyan Localization

- Currency: KSh (Kenyan Shillings)
- Timezone: Africa/Nairobi
- Delivery: Nairobi standard 2-3 days
- Phone format: 254XXXXXXX or 0XXXXXXX
- M-Pesa: Full Daraja API support
- Swahili: Error messages include Swahili translations

---

**Version**: 1.0.0  
**Last Updated**: February 6, 2025  
**Python**: 3.10+  
**Django**: 5.1+
