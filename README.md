# IQtestWithPoliticalPreference

This project provides an IQ quiz and political preference survey using a mobile‑first freemium design. The original Flask code has been moved to `legacy_flask_app.py`. The new stack uses **FastAPI** for the backend and a **React** single‑page application for the frontend.

## Backend (FastAPI)

- Located in `backend/`.
- Install dependencies with `pip install -r backend/requirements.txt`.
- Run locally using:
  ```bash
  uvicorn backend.main:app --reload
  ```
- Environment variables (see `.env.example`):
  - `DATABASE_URL` – Supabase Postgres connection string.
  - `SUPABASE_API_KEY` – API key for Supabase.
  - `SMS_PROVIDER` – `twilio` (default) or `sns` for Amazon SNS.
  - When using Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_VERIFY_SERVICE_SID`.
  - When using SNS: `AWS_REGION` and AWS credentials configured in the environment.
  - `PAYPAY_API_KEY` or `LINEPAY_API_KEY` – enable local payment gateways in Japan.
  - The backend logs an estimated cost for each OTP sent based on the selected SMS provider.
  - `STRIPE_API_KEY` – Stripe secret key for payments.
  - `PHONE_SALT` – salt for hashing phone or email identifiers.
  - `MAX_FREE_ATTEMPTS` – number of free quiz attempts allowed before payment is required (default `1`).
- OTP endpoints: `/auth/request-otp` and `/auth/verify-otp` support SMS via Twilio or SNS and fallback email codes through Supabase. Identifiers are hashed with per-record salts.
- Quiz endpoints: `/quiz/start` returns a random set of questions from `backend/data/iq_pool/`; `/quiz/submit` accepts answers and records a play. Optional query `question_set_id` selects a specific pool file.
- Adaptive endpoints: `/adaptive/start` begins an adaptive quiz and `/adaptive/answer` returns the next question until the ability estimate stabilizes.
- Pricing endpoints: `/pricing/{id}` shows the dynamic price for a user, `/play/record` registers a completed play and `/referral` adds a referral credit.
- The question bank with psychometric metadata lives in `backend/data/question_bank.json`. Run `tools/generate_questions.py` to create new items with the `o3pro` model. The script filters out content resembling proprietary IQ tests.
- Additional sets can be placed in `backend/data/iq_pool/`. Ensure each file is
  manually reviewed before use. The helper `tools/generate_iq_questions.py` can
  create new items in this format.
  To regenerate questions:
  ```bash
  OPENAI_API_KEY=your-key python tools/generate_questions.py -n 60
  ```
  The JSON output is saved to `backend/data/question_bank.json` with sequential `id` values.
  To create a new pool file with the updated generator:
  ```bash
  OPENAI_API_KEY=your-key python tools/generate_iq_questions.py -n 50 -o new_items.json
  ```
  After reviewing `new_items.json`, move it into `backend/data/iq_pool/`.

## Frontend (React)

- Located in `frontend/` and built with Vite, React Router, Tailwind CSS and framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.
- The app is intended for smartphones. A `MobileOnlyWrapper` component blocks
  desktop browsers with a friendly message. Disable or adjust this behaviour by
  editing `frontend/src/MobileOnlyWrapper.jsx`.
- Basic anti-cheat measures disable text selection, render questions on a canvas
  and watermark the screen. They cannot fully prevent screenshots.

To deploy on serverless hosting, point the platform to `backend/main.py` and serve the built frontend from `frontend/dist`. Environment variables configure SMS and payment providers so you can select the cheapest option for each region.

This repository now serves as a starting point for the revamped freemium quiz platform. Terms of Service and a Privacy Policy are provided under `templates/` and personal identifiers are hashed with per-record salts. Aggregated statistics apply differential privacy noise for research use only.

## Services and Costs

- **SMS verification:** configurable between Twilio and Amazon SNS. Choose the provider with the best local rates.
- **Email OTP:** provided free via Supabase auth as a fallback for users without SMS.
- **Serverless hosting:** deploy FastAPI on platforms such as Vercel or Cloudflare Workers. Supabase provides the managed Postgres database and authentication layer.
- **Payments:** Stripe is used by default but the `/pricing` API enables switching to local processors like PayPay or Line Pay with minimal code changes.
- **Analytics:** the `/analytics` endpoint logs anonymous events to a self-hosted solution, avoiding third-party trackers.
