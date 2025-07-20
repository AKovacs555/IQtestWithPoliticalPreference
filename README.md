# IQtestWithPoliticalPreference

This project provides an IQ quiz and political preference survey using a mobile‑first freemium design. The original Flask code has been moved to `legacy_flask_app.py`. The new stack uses **FastAPI** for the backend and a **React** single‑page application for the frontend.

## Backend (FastAPI)

- Located in `backend/`.
- Install dependencies with `pip install -r backend/requirements.txt`.
- Run locally using:
  ```bash
  uvicorn backend.main:app --reload
  ```
- Environment variables:
  - `DATABASE_URL` – Supabase Postgres connection string.
  - `SUPABASE_API_KEY` – API key for Supabase.
  - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_VERIFY_SERVICE_SID` – Twilio Verify credentials.
  - `STRIPE_API_KEY` – Stripe secret key for payments.
  - `PHONE_SALT` – salt for hashing phone numbers.

## Frontend (React)

- Located in `frontend/` and built with Vite, React Router, Tailwind CSS and framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.

This repository now serves as a starting point for the revamped freemium quiz platform.
