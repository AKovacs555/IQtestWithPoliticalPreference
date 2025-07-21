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
  - `STRIPE_PUBLISHABLE_KEY` – Stripe public key for the client.
  - `PHONE_SALT` – salt for hashing phone or email identifiers.
  - `MAX_FREE_ATTEMPTS` – number of free quiz attempts allowed before payment is required (default `1`).
  - `RETRY_PRICE_TIERS` – comma separated yen prices for paid retries.
  - `PRO_PRICE_MONTHLY` – monthly cost of the optional subscription.
  - `DP_EPSILON` – epsilon used when adding Laplace noise to aggregated data.
  - `DATA_API_KEY` – authentication token for the paid differential‑privacy API.
  - `SUPABASE_URL` – base URL for Supabase (required for share images).
  - `SUPABASE_SHARE_BUCKET` – bucket name for storing generated share images.
  - `ADMIN_API_KEY` – token for admin endpoints such as normative updates.
- OTP endpoints: `/auth/request-otp` and `/auth/verify-otp` support SMS via Twilio or SNS and fallback email codes through Supabase. Identifiers are hashed with per-record salts.
- Quiz endpoints: `/quiz/start` returns a random set of questions from `backend/data/iq_pool/`; `/quiz/submit` accepts answers and records a play. Optional query `question_set_id` selects a specific pool file.
- Adaptive endpoints: `/adaptive/start` begins an adaptive quiz and `/adaptive/answer` returns the next question until the ability estimate stabilizes.
- Pricing endpoints: `/pricing/{id}` shows the dynamic price for a user, `/play/record` registers a completed play and `/referral` adds a referral credit.
- Demographic and party endpoints: `/user/demographics` records age, gender and income band. `/user/party` stores supported parties and enforces monthly change limits.
- Aggregated data is available via `/leaderboard` and the authenticated `/data/iq` endpoint which returns differentially private averages.
- The question bank with psychometric metadata lives in `backend/data/question_bank.json`. Run `tools/generate_questions.py` to create new items with the `o3pro` model. The script filters out content resembling proprietary IQ tests.
  - Additional sets can be placed in `backend/data/iq_pool/`. Ensure each file is
    manually reviewed before use. The helper `tools/generate_iq_questions.py` can
    create new items in this format. It accepts `--n`, `--start_id` and
    `--outfile` arguments and validates IDs to avoid collisions.
  To regenerate questions:
  ```bash
  OPENAI_API_KEY=your-key python tools/generate_questions.py -n 60
  ```
  The JSON output is saved to `backend/data/question_bank.json` with sequential `id` values.
  To create a new pool file with the updated generator or your own prompt:
  ```bash
  OPENAI_API_KEY=your-key python tools/generate_iq_questions.py -n 50 -o new_items.json
  ```
  After reviewing `new_items.json`, move it into `backend/data/iq_pool/`.

## Frontend (React)

 - Located in `frontend/` and built with Vite, React Router, Tailwind CSS with DaisyUI components and framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.
- The UI is smartphone only. `MobileOnlyWrapper` checks the user agent and screen
  width to redirect desktop visitors. Adjust the behaviour in
  `frontend/src/MobileOnlyWrapper.jsx`.
- Basic anti-cheat measures disable text selection, draw questions on a canvas
  and apply a watermark. Comments note that screenshots cannot be fully blocked.

To deploy on serverless hosting, point Vercel to `frontend` for the React build
and Render (or another provider) to `backend/main.py`. Provide the environment
variables below to both platforms. After pushing to GitHub, redeployments will
occur automatically.

This repository now serves as a starting point for the revamped freemium quiz platform. Terms of Service and a Privacy Policy are provided under `templates/` and personal identifiers are hashed with per-record salts. Aggregated statistics apply differential privacy noise for research use only.

## Monetisation model

- Users get **one free play**. Further attempts follow a paid retry ladder. The
  `/pricing/{user}` endpoint reveals the next price tier based on previous
  plays.
- A **Pro Pass** subscription (configurable via `PRO_PRICE_MONTHLY`) grants
  multiple plays per month and early access to new question sets.
- Each account has a **referral code**. When someone signs up with that code
  both parties receive a free retry credit (`/referral`).
- Business customers can request aggregated data via the `/leaderboard`
  endpoint once differential privacy safeguards are implemented.

## Services and Costs

- **SMS verification:** configurable between Twilio and Amazon SNS. Choose the provider with the best local rates.
- **Email OTP:** provided free via Supabase auth as a fallback for users without SMS.
- **Serverless hosting:** deploy FastAPI on platforms such as Vercel or Cloudflare Workers. Supabase provides the managed Postgres database and authentication layer.
- **Payments:** Stripe is used by default but the `/pricing` API enables switching to local processors like PayPay or Line Pay with minimal code changes.
- **Analytics:** the `/analytics` endpoint logs anonymous events to a self-hosted solution, avoiding third-party trackers.

## Share image generation

When a quiz is completed the backend creates a branded result image using Pillow. The image is uploaded to the Supabase bucket defined by `SUPABASE_SHARE_BUCKET` and the public URL is returned alongside the score. The frontend sets Open Graph and Twitter meta tags with this URL so that shared links display the personalised card.

## Updating the normative distribution

IQ percentiles rely on `backend/data/normative_distribution.json`. Trigger the `/admin/update-norms` endpoint weekly with `ADMIN_API_KEY` to append recent scores and keep only the latest 5000 values.
