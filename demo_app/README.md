# AI Software Tester — Demo App

A minimal Flask web application for demonstrating the AI Software Tester capabilities.

## Running the Demo App

```bash
cd demo_app
pip install flask
python app.py
```

The app runs at `http://localhost:5000`

## Test Credentials

| Email | Password | Name |
|-------|----------|------|
| test@example.com | Test123! | Test User |
| admin@example.com | Admin123! | Admin User |
| demo@test.com | any_password | Demo User |

## Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Login page |
| `/login` | GET, POST | Login page and handler |
| `/register` | GET, POST | Registration page and handler |
| `/dashboard` | GET | Dashboard (requires login) |
| `/logout` | GET | Logout |
| `/api/login` | POST | JSON API login |
| `/api/register` | POST | JSON API registration |
| `/api/health` | GET | Health check |
| `/api/users` | GET | List registered users |

## Intentional Bugs

See [BUGS.md](BUGS.md) for full documentation of all 4 intentional bugs.
