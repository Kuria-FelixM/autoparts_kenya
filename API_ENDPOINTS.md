# AutoParts Kenya API - Complete Endpoints Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Use JWT Bearer token:
```
Authorization: Bearer <access_token>
```

---

## 🔓 PUBLIC ENDPOINTS (No Authentication)

### Users - Registration & Authentication
```
POST   /users/register/                      # Create new account
POST   /users/token/                         # Get JWT token
POST   /users/token/refresh/                 # Refresh token
```

### Vehicles (Public Read)
```
GET    /vehicles/makes/                      # List all makes
GET    /vehicles/makes/{id}/                 # Get make details
GET    /vehicles/models/                     # List all models
GET    /vehicles/models/{id}/                # Get model details
GET    /vehicles/models/?make={id}           # Filter models by make
GET    /vehicles/models/?year_from=2015      # Filter by year range
```

### Products (Public Read)
```
GET    /products/categories/                 # List categories
GET    /products/categories/{id}/            # Get category details
GET    /products/products/                   # List products
GET    /products/products/{id}/              # Get product details
GET    /products/products/featured/          # Get featured products
GET    /products/products/by_vehicle/        # Filter by vehicle
       ?vehicle_year=2020&vehicle_make=1&vehicle_model=5
GET    /products/products/                   # Advanced filters
       ?vehicle_year=2020
       &price_min=500
       &price_max=5000
       &category=1
       &in_stock=true
       &search=oil+filter
       &ordering=price
```

### Orders - Guest Checkout
```
POST   /orders/checkout/                     # Create order (guest or auth)
GET    /orders/order/{order_number}/         # View any order by number
```

### Payments - M-Pesa
```
POST   /payments/initiate-stk-push/          # Start M-Pesa payment
POST   /payments/mpesa-callback/             # M-Pesa webhook (Safaricom)
```

---

## 🔐 AUTHENTICATED USER ENDPOINTS

### Users - Profile Management
```
GET    /users/profile/                       # Get authenticated user profile
PATCH  /users/profile/                       # Update profile
```

### Users - Saved Vehicles
```
GET    /users/saved-vehicles/                # List saved vehicles
POST   /users/saved-vehicles/                # Save new vehicle
GET    /users/saved-vehicles/{id}/           # Get vehicle details
PATCH  /users/saved-vehicles/{id}/           # Update vehicle
DELETE /users/saved-vehicles/{id}/           # Delete vehicle
POST   /users/saved-vehicles/{id}/set_primary/ # Set as primary
```

### Users - Saved Addresses
```
GET    /users/saved-addresses/               # List saved addresses
POST   /users/saved-addresses/               # Save new address
GET    /users/saved-addresses/{id}/          # Get address details
PATCH  /users/saved-addresses/{id}/          # Update address
DELETE /users/saved-addresses/{id}/          # Delete address
POST   /users/saved-addresses/{id}/set_default/ # Set as default
```

### Orders - Order History
```
GET    /orders/my-orders/                    # Get my orders
GET    /orders/my-orders/?order_status=paid  # Filter by status
GET    /orders/order/{order_number}/         # Get my order details
```

### Payments - Status Check
```
GET    /payments/check-status/?order_id=1    # Check payment status
```

---

## 👑 OWNER-ONLY ENDPOINTS (is_owner=True)

### Vehicles - Write Access
```
POST   /vehicles/makes/                      # Create make
PATCH  /vehicles/makes/{id}/                 # Update make
DELETE /vehicles/makes/{id}/                 # Delete make
POST   /vehicles/models/                     # Create model
PATCH  /vehicles/models/{id}/                # Update model
DELETE /vehicles/models/{id}/                # Delete model
```

### Products - Full Management
```
POST   /products/categories/                 # Create category
PATCH  /products/categories/{id}/            # Update category
DELETE /products/categories/{id}/            # Delete category
POST   /products/products/                   # Create product
PATCH  /products/products/{id}/              # Update product
DELETE /products/products/{id}/              # Delete product
```

### Orders - Admin Management
```
GET    /orders/admin/orders/                 # List ALL orders
GET    /orders/admin/orders/{id}/            # Get order details
PATCH  /orders/admin/orders/{id}/            # Update order status
```

### Analytics - Dashboard & Reports (Owner-only)
```
GET    /analytics/dashboard/                 # Key metrics (revenue, orders, products, stock)
GET    /analytics/revenue/                   # Revenue by period
GET    /analytics/top-products/              # Best selling products
GET    /analytics/top-products/?limit=20     # Custom limit
GET    /analytics/low-stock/                 # Low inventory alert
GET    /analytics/low-stock/?threshold=5     # Custom threshold
GET    /analytics/order-status/              # Order status distribution
GET    /analytics/payment-status/            # Payment status distribution
GET    /analytics/profit/                    # Profit margin analysis
```

---

## 📝 Request/Response Examples

### Example 1: Guest Checkout
```bash
curl -X POST http://localhost:8000/api/v1/orders/checkout/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 3, "quantity": 1}
    ],
    "delivery_address": "123 Kenyatta Avenue, Nairobi",
    "delivery_city": "Nairobi",
    "recipient_name": "John Doe",
    "recipient_phone": "+254712345678",
    "guest_email": "john@example.com",
    "customer_notes": "Leave with security if not home",
    "delivery_type": "standard"
  }'
```

**Response:**
```json
{
  "order": {
    "id": 1,
    "order_number": "ORD-20250206144530",
    "total_amount": "5450.00",
    "payment_status": "unpaid",
    "order_status": "pending",
    "items": [
      {
        "product_name": "Engine Oil Filter",
        "quantity": 2,
        "unit_price": "950.00",
        "line_total": "1900.00"
      }
    ]
  },
  "message": "Agizo limejifungua! Kuendelea na malipo.",
  "next_step": "/api/v1/payments/initiate-stk-push/?order_id=1"
}
```

### Example 2: Register & Get Token
```bash
# Register
curl -X POST http://localhost:8000/api/v1/users/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "password_confirm": "SecurePass123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+254712345678"
  }'

# Get token
curl -X POST http://localhost:8000/api/v1/users/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123"
  }'
```

### Example 3: Filter Products by Vehicle
```bash
curl -X GET "http://localhost:8000/api/v1/products/products/?vehicle_year=2020&price_min=500&price_max=5000&in_stock=true" \
  -H "Accept: application/json"
```

### Example 4: M-Pesa Payment Initiation
```bash
curl -X POST http://localhost:8000/api/v1/payments/initiate-stk-push/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "phone_number": "+254712345678"
  }'
```

**Response:**
```json
{
  "success": true,
  "merchant_request_id": "29115-37770150-1",
  "checkout_request_id": "ws_CO_190322141651829148",
  "response_message": "Success. Request accepted for processing",
  "message": "STK Push imetumwa simu. Tafadhali angalia simu na ingiza PIN."
}
```

### Example 5: Owner Analytics - Dashboard
```bash
curl -X GET http://localhost:8000/api/v1/analytics/dashboard/ \
  -H "Authorization: Bearer <token>"
```

**Response:**
```json
{
  "total_revenue": 245000.50,
  "total_revenue_currency": "KSh",
  "total_orders": 47,
  "orders_today": 3,
  "total_products": 156,
  "low_stock_products": 12,
  "low_stock_threshold": 10,
  "generated_at": "2025-02-06T14:45:30.123456Z"
}
```

---

## ⚙️ Query Parameters

### Pagination (All List Endpoints)
```
?page=1          # Page number (default: 1)
?page_size=50    # Items per page (default: 20)
```

### Search (Products, Categories, Vehicles)
```
?search=oil      # Search by name/description/sku
```

### Ordering (All List Endpoints)
```
?ordering=price              # Ascending
?ordering=-created_at        # Descending (newer first)
```

### Filtering
```
/products/products/?category=1&in_stock=true
/vehicles/models/?make=1&year_from=2015
/orders/my-orders/?order_status=delivered&payment_status=paid
```

---

## 🔄 Status Values

### Order Status
- `pending` - Newly created
- `confirmed` - Payment confirmed
- `processing` - Being prepared
- `shipped` - On delivery
- `delivered` - Received by customer
- `cancelled` - Cancelled

### Payment Status
- `unpaid` - No payment yet
- `pending` - Awaiting M-Pesa confirmation
- `paid` - Payment successful
- `failed` - Payment failed
- `refunded` - Refunded

### Vehicle Compatibility
- Year-based: Products automatically compatible with a year if `year_from <= requested_year <= year_to`

---

## 🛑 HTTP Status Codes

- **200 OK** - Request successful
- **201 Created** - Resource created
- **204 No Content** - Deleted successfully
- **400 Bad Request** - Validation error
- **401 Unauthorized** - Missing/invalid token
- **403 Forbidden** - Owner-only access denied
- **404 Not Found** - Resource not found
- **500 Server Error** - Internal error

---

## 📍 Documentation

- **Swagger/OpenAPI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema**: http://localhost:8000/api/schema/

---

**Last Updated**: February 6, 2025
