# Sample Data Guide - AutoParts Kenya

This guide explains how to load sample/fixture data into your AutoParts Kenya database.

## 📁 Fixture Files

Sample data fixtures are provided in the following locations:

```
vehicles/fixtures/vehicles_initial_data.json    # Vehicle makes and models
products/fixtures/products_initial_data.json    # Product categories and products
users/fixtures/users_initial_data.json          # Users and profiles
```

## 🔧 Loading Fixtures

### Option 1: Load All Fixtures at Once

```bash
# Activate your virtual environment
source venv/bin/activate

# Load all fixtures
python manage.py loaddata vehicles_initial_data.json products_initial_data.json users_initial_data.json
```

### Option 2: Load Individual Fixtures

```bash
# Load vehicles first (recommended order)
python manage.py loaddata vehicles_initial_data.json

# Load products
python manage.py loaddata products_initial_data.json

# Load users
python manage.py loaddata users_initial_data.json
```

### Option 3: Django Admin Interface

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Visit: http://localhost:8000/admin/

3. Login with superuser (admin/admin)

4. Navigate to relevant sections and add data manually

## 📊 What's Included in Sample Data

### Vehicles (vehicles_initial_data.json)
- **8 Vehicle Makes**: Toyota, Nissan, Mercedes-Benz, BMW, Hyundai, Suzuki, Isuzu, Ford
- **16 Vehicle Models**: Corolla, Camry, Hilux, Altima, Primera, C-Class, 3 Series, etc.
- Year ranges for compatibility (e.g., 2010-2025)

### Products (products_initial_data.json)
- **8 Product Categories**:
  - Engine Oil
  - Air Filters
  - Brake Systems
  - Batteries
  - Spark Plugs
  - Belts & Hoses
  - Suspension Parts
  - Lighting

- **16 Sample Products**:
  - Motul 5W-30 Synthetic Engine Oil (KSh 2,450)
  - Toyota Original Air Filter (KSh 950)
  - Brake Pad Set for Toyota Corolla (KSh 3,500)
  - Car Battery 60Ah Premium (KSh 5,800)
  - And more...

- All products include:
  - SKU codes
  - Pricing (sale & cost)
  - Stock quantities
  - Reorder levels
  - Vehicle compatibility (year ranges)
  - Featured flags

### Users (users_initial_data.json)
- **Admin User**: admin (superuser)
- **Test Users**:
  - john_doe (regular customer)
  - jane_smith (regular customer)
  - mike_owner (owner/staff user)

> **Note**: Passwords in fixtures are hashed and are placeholders. For production, use Django's `createsuperuser` command instead.

## 🛍️ Testing with Sample Data

### 1. View Products via API

```bash
# List all products
curl http://localhost:8000/api/v1/products/products/

# Filter by category
curl "http://localhost:8000/api/v1/products/products/?category=1"

# Get featured products
curl http://localhost:8000/api/v1/products/products/featured/
```

### 2. View Vehicles

```bash
# List all makes
curl http://localhost:8000/api/v1/vehicles/makes/

# List models for a make
curl "http://localhost:8000/api/v1/vehicles/models/?make=1"

# Filter by year
curl "http://localhost:8000/api/v1/vehicles/models/?year_from=2010"
```

### 3. Create Test Orders

```bash
# Guest checkout
curl -X POST http://localhost:8000/api/v1/orders/checkout/ \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 4, "quantity": 1}
    ],
    "delivery_address": "123 Kenyatta Avenue, Nairobi",
    "delivery_city": "Nairobi",
    "recipient_name": "John Doe",
    "recipient_phone": "+254712345678",
    "guest_email": "john@example.com",
    "delivery_type": "standard"
  }'
```

## 🗑️ Clearing Data

To reset the database and remove all fixture data:

```bash
# WARNING: This will delete all data!
python manage.py flush

# Confirm when prompted
# Then reload fixtures
python manage.py loaddata vehicles_initial_data.json products_initial_data.json users_initial_data.json
```

## 📝 Creating Custom Fixtures

To export current database state as a fixture:

```bash
# Export all data
python manage.py dumpdata > backup.json

# Export specific app
python manage.py dumpdata products > products_backup.json

# Export specific model
python manage.py dumpdata products.category > categories_backup.json
```

## 🔐 Security Notes

⚠️ **Important**: The user fixtures included are for development/testing only:
- Passwords are dummy/hashed placeholders
- Do NOT use these credentials in production
- Always create new admin users with `python manage.py createsuperuser`
- Never commit real credentials to version control

## ✅ Verification Checklist

After loading fixtures, verify:

- [ ] 8 Vehicle Makes loaded
- [ ] 16 Vehicle Models loaded
- [ ] 8 Product Categories loaded
- [ ] 16 Products loaded
- [ ] 4 Users created
- [ ] Admin user accessible at http://localhost:8000/admin/
- [ ] API endpoints return data: http://localhost:8000/api/v1/products/products/
- [ ] Products have stock counts > 0
- [ ] Featured products are marked

## 🆘 Troubleshooting

### Fixture Not Found
```
FileNotFoundError: No file at /path/to/fixture
```
**Solution**: Ensure fixture files are in the correct directory:
- `app/fixtures/filename.json`

### Fixture Already Exists
```
IntegrityError: duplicate key value violates unique constraint
```
**Solution**: Clear the database first with `python manage.py flush`

### Import Order Error
**Solution**: Load fixtures in order:
1. vehicles_initial_data.json
2. products_initial_data.json
3. users_initial_data.json

## 📚 Additional Resources

- [Django Fixtures Documentation](https://docs.djangoproject.com/en/stable/howto/initial-data/)
- [API Documentation](API_ENDPOINTS.md)
- [Installation Guide](INSTALLATION.md)

---

**Last Updated**: February 18, 2025
