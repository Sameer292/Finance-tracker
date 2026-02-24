# Expensia - Finance Tracker API

A robust RESTful API built with FastAPI for personal finance management. Expensia enables users to track their income and expenses, categorize transactions, and monitor their financial health through a clean, secure backend service.

## Features

- **User Authentication**: Secure registration and login with JWT-based access and refresh tokens
- **Transaction Management**: Full CRUD operations for income and expense tracking
- **Category System**: Custom categories with color and icon support
- **Financial Overview**: Automatic balance tracking with total income and expenses
- **Date Filtering**: Filter transactions by custom date ranges
- **RESTful Design**: Clean API architecture following best practices

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLAlchemy ORM with SQLite
- **Authentication**: JWT (PyJWT) with Argon2 password hashing
- **Migration**: Alembic
- **Validation**: Pydantic
- **Testing**: pytest, httpx

## Getting Started

### Prerequisites

- Python 3.12+

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Sameer292/Finance-tracker.git
cd Finance-tracker
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
JWT_SECRET=your_secure_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRY_DAYS=7
DATABASE_URL=sqlite:///./financeTracker.db
```

5. Run the server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new user |
| POST | `/login` | Login and receive tokens |
| POST | `/refresh` | Refresh access token |
| GET | `/me` | Get current user info |
| PATCH | `/change-password` | Change user password |
| PATCH | `/update-profile` | Update user profile |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | Get all transactions (with optional date filtering) |
| GET | `/transactions/recent` | Get recent transactions (last 3 days) |
| GET | `/transactions/{id}` | Get a specific transaction |
| POST | `/transactions` | Create a new transaction |
| PUT | `/transactions/{id}` | Update a transaction |
| DELETE | `/transactions/{id}` | Delete a transaction |
| DELETE | `/transactions` | Delete all transactions |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | Get all categories |
| GET | `/category/{id}` | Get a specific category |
| GET | `/category/{id}/transactions` | Get transactions in a category |
| POST | `/categories` | Create a new category |
| DELETE | `/category/{id}` | Delete a category |

## Request/Response Examples

### Register User

```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepassword123"
  }'
```

### Create Transaction

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "expense",
    "amount": 50.00,
    "note": "Grocery shopping",
    "category_id": 1,
    "transaction_date": "2026-02-24T10:00:00"
  }'
```

## Project Structure

```
FinanceTracker/
├── main.py                 # Application entry point
├── pyproject.toml          # Project dependencies
├── alembic.ini             # Alembic configuration
├── db/
│   ├── database.py         # Database connection
│   └── models.py          # SQLAlchemy models
├── routes/
│   ├── authRoutes.py      # Authentication endpoints
│   ├── transactionRoutes.py # Transaction endpoints
│   └── categoryRoutes.py  # Category endpoints
├── schemas/
│   ├── authSchemas.py     # Authentication schemas
│   ├── TransactionSchemas.py # Transaction schemas
│   └── categorySchemas.py # Category schemas
├── middlewares/
│   └── authMiddleWare.py  # JWT authentication middleware
├── utils/
│   └── utils.py           # Utility functions
├── src/
│   └── settings.py        # Application settings
└── alembic/
    └── versions/          # Database migrations
```

## Testing

Run the test suite:

```bash
pytest
```

## License

MIT License

## Author

Sameer Paudel
- GitHub: [@sameer292](http://github.com/sameer292)
- Email: paudelsameer888@gmail.com
