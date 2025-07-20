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
  - `PHONE_SALT` – salt for hashing phone numbers (used as fallback).
- OTP endpoints: `/auth/request-otp` and `/auth/verify-otp` store phone numbers with per-record salts.
- Quiz endpoints: `/quiz/start` returns 20 questions; `/quiz/submit` accepts answers and returns a score.
- Adaptive endpoints: `/adaptive/start` begins an adaptive quiz and `/adaptive/answer` returns the next question until the ability estimate stabilizes.
- The question bank with psychometric metadata lives in `backend/data/question_bank.json`. Use `tools/generate_questions.py` to regenerate items via the `o3pro` model.

## Frontend (React)

- Located in `frontend/` and built with Vite, React Router, Tailwind CSS and framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.

This repository now serves as a starting point for the revamped freemium quiz platform.
