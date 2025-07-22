# IQtestWithPoliticalPreference

This project provides an IQ quiz and political preference survey using a responsive freemium design. The original Flask code has been moved to `legacy_flask_app.py`. The new stack uses **FastAPI** for the backend and a **React** single‑page application for the frontend. The UI now uses **Material UI** components with Tailwind utilities and works on mobile and desktop devices.

## Backend (FastAPI)

- Located in `backend/`.
- Install dependencies with `pip install -r backend/requirements.txt`.
  This includes `pillow` for generating share images.
- When the working directory is `frontend/` (e.g. serverless build steps),
  a `frontend/backend` symlink points back to the root backend folder so the
  same command still works.
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
  - `STRIPE_SECRET_KEY` – Stripe secret key for payments.
  - `STRIPE_PUBLISHABLE_KEY` – Stripe public key for the client.
  - `PHONE_SALT` – salt for hashing phone or email identifiers.
  - `MAX_FREE_ATTEMPTS` – number of free quiz attempts allowed before payment is required (default `1`).
  - `RETRY_PRICE_TIERS` – comma separated yen prices for paid retries.
  - `PRO_PRICE_MONTHLY` – monthly cost of the optional subscription.
  - `DP_EPSILON` – epsilon used when adding Laplace noise to aggregated data.
  - `DP_MIN_COUNT` – minimum records required before an aggregate is reported.
  - `DATA_API_KEY` – authentication token for the paid differential‑privacy API.
  - `SUPABASE_URL` – base URL for Supabase (required for share images).
  - `SUPABASE_SHARE_BUCKET` – bucket name for storing generated share images.
  - `ADMIN_API_KEY` – token for admin endpoints such as normative updates.
  - `AD_UNIT_ID_ANDROID`, `AD_UNIT_ID_IOS`, `ADMOB_APP_ID` – Google AdMob ad identifiers.
  - `AD_REWARD_POINTS` – points awarded per ad view.
  - `RETRY_POINT_COST` – points required for an extra attempt.
  - `VITE_API_BASE` – base URL of the backend API for the React app.
  - `VITE_STRIPE_PUBLISHABLE_KEY` – public Stripe key used by the frontend.

## 環境設定

Supabase、Stripe、AWS SNS、Google AdMob のアカウントを作成し、それぞれのダッシュボードから API キーを取得してください。取得したキーは Vercel または Render の環境変数に設定します。

- [Supabase ドキュメント](https://supabase.com/docs)
- [Stripe ドキュメント](https://stripe.com/docs)
- [AWS SNS ドキュメント](https://docs.aws.amazon.com/sns)
- [Google AdMob ドキュメント](https://developers.google.com/admob)

- Supabase: Settings > API で URL と service role キーをコピー
- Stripe: ダッシュボードの 開発者 > API キー から取得
- Google AdMob: アプリ ID と広告ユニット ID を作成してコピー
- AWS SNS: IAM ユーザーのアクセスキーを使用
### 広告設定

1. AdMob コンソールでアプリを登録し、報酬付き動画広告ユニットを作成します。
2. 取得した **アプリ ID** と **広告ユニット ID (Android/iOS)** を `.env` の
   `ADMOB_APP_ID`, `AD_UNIT_ID_ANDROID`, `AD_UNIT_ID_IOS` に設定します。
3. 同じ値を Vercel または Render の環境変数にも追加してください。
4. アドネットワークに広告が表示されるまで数時間かかる場合があります。

AWS SNS を利用する場合は IAM コンソールでアクセスキーを発行し、
`AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` を設定します。
- OTP endpoints: `/auth/request-otp` and `/auth/verify-otp` support SMS via Twilio or SNS and fallback email codes through Supabase. Identifiers are hashed with per-record salts.
- Quiz endpoints: `/quiz/start` returns a random set of questions from the `questions/` directory; `/quiz/submit` accepts answers and records a play. Optional query `set_id` selects a specific set file. `/quiz/sets` lists the available set IDs for the frontend.
- Adaptive endpoints: `/adaptive/start` begins an adaptive quiz and `/adaptive/answer` returns the next question until the ability estimate stabilizes.
- Pricing endpoints: `/pricing/{id}` shows the dynamic price for a user, `/play/record` registers a completed play and `/referral` adds a referral credit.
- Demographic and party endpoints: `/user/demographics` records age, gender and income band. `/user/party` stores supported parties and enforces monthly change limits.
- Aggregated data is available via `/leaderboard` and the authenticated `/data/iq` endpoint which returns differentially private averages.
- The question bank with psychometric metadata lives in `backend/data/question_bank.json`. Use `tools/generate_questions.py --import_dir=generated_questions` to merge question files you created with ChatGPT.
 - Individual question sets for the live quiz are stored under `questions/`. Each file must conform to `questions/schema.json` and can be fetched via `/quiz/start?set_id=set01`.
- The backend reads these JSON files at runtime so new sets can be added via GitHub without redeploying the API.
  - Additional sets can simply be placed in the top-level `questions/` directory. Each file is validated against `schema.json` on startup so redeploy is unnecessary. Ensure all items are
    manually reviewed before use. The helper `tools/generate_iq_questions.py` can
    create new items in this format. It accepts `--n`, `--start_id` and
    `--outfile` arguments and validates IDs to avoid collisions.
  Prepare question files under `generated_questions/` and run:
  ```bash
  python tools/generate_questions.py --import_dir=generated_questions
  ```
  Each imported file must contain a JSON array of objects with `text`, `options`,
  `correct_index` and an `irt` object. IDs are assigned automatically and the
  script reports how many easy, medium and hard questions were added.

### Creating questions with ChatGPT

Copy the following prompt into ChatGPT to generate a set of items:

```
Please create 10 'easy' IQ test questions that assess verbal, numerical, and spatial reasoning.
Each question should include:
  - text: the question statement (in Japanese)
  - options: four answer options (A, B, C, D)
  - correct_index: the zero-based index (0–3) of the correct answer
Do not reuse copyrighted content or known test items.
Return the questions as a JSON array.
```

Save the output to `generated_questions/easy_01.json` and add provisional IRT
parameters. Use `{"a": 1.0, "b": -0.7}` for easy, `{"a": 1.0, "b": 0.0}` for
medium and `{"a": 1.0, "b": 0.7}` for hard questions.

## Frontend (React)

 - Located in `frontend/` and built with Vite, React Router, Tailwind CSS and Material UI components with framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.
- The UI uses a responsive layout. The previous mobile restriction was removed and
  `MobileOnlyWrapper` now simply renders its children.
- Basic anti-cheat measures disable text selection, draw questions on a canvas
  and apply a watermark. Comments note that screenshots cannot be fully blocked.
- React components are organised under `src/components` and `src/pages` for clarity.
- A new `Leaderboard` page displays average IQ by party using the `/leaderboard` API.
- Users can toggle between light and dark themes using the button in the navbar.
- Translations live under `frontend/translations/` and are loaded via `src/i18n.js`.
  Vite's config enables JSON imports so new languages can be added without code changes.
- The landing page uses framer-motion for parallax scrolling and animated calls to action, while quiz pages feature progress bars and confetti on completion.

To deploy on serverless hosting, point Vercel to `frontend` for the React build
and Render (or another provider) to `backend/main.py`. Provide the environment
variables below to both platforms. After pushing to GitHub, redeployments will
occur automatically.

On Render create a **Web Service** from this repository and copy the variables
from `.env.example` into the dashboard. On Vercel configure the same values
under *Project Settings → Environment Variables*. Both services will pick up
changes on each commit and redeploy automatically.

This repository now serves as a starting point for the revamped freemium quiz platform. Terms of Service and a Privacy Policy are provided under `templates/` and personal identifiers are hashed with per-record salts. Aggregated statistics apply differential privacy noise for research use only.

## Monetisation model

- Users get **one free play**. Further attempts follow a paid retry ladder. The
  `/pricing/{user}` endpoint reveals the next price tier based on previous
  plays.
- A **Pro Pass** subscription (configurable via `PRO_PRICE_MONTHLY`) grants
  multiple plays per month and early access to new question sets.
- Each account has a **referral code**. When someone signs up with that code
  both parties receive a free retry credit (`/referral`).
- Rewarded ads via `/ads/start` and `/ads/complete` grant `AD_REWARD_POINTS`. Check `/points/{id}` for the balance and spend `RETRY_POINT_COST` points when calling `/play/record`.
- Promotional codes can be configured via the admin API to offer temporary discounts.
- Business customers can request aggregated data via the `/leaderboard`
  endpoint once differential privacy safeguards are implemented.

## Points System

Users earn points by watching rewarded ads via `/ads/start` and `/ads/complete`.
The balance is returned from `/points/{user_id}` and `RETRY_POINT_COST` points
can substitute payment when calling `/play/record`. 1 point is granted per ad
view by default (`AD_REWARD_POINTS`).

## Question schema

Question sets in `questions/` follow `questions/schema.json`:

```json
{
  "id": "set01",
  "language": "en",
  "title": "Sample",
  "questions": [
    {"id": 0, "question": "?", "options": ["A", "B"], "answer": 1,
     "irt": {"a": 1.0, "b": 0.0}}
  ]
}
```

Files are validated on startup so new sets can be committed without redeploying.

## Internationalisation

All strings reside under `frontend/translations/` and are loaded by
`src/i18n.js`. English and Japanese locales are provided. Add new languages by
creating a JSON file in that folder and updating `i18n.js`. The UI supports RTL
languages using the `dir` attribute on the root element.

## Services and Costs

- **SMS verification:** configurable between Twilio and Amazon SNS. Choose the provider with the best local rates.
- **Email OTP:** provided free via Supabase auth as a fallback for users without SMS.
- **Serverless hosting:** deploy FastAPI on platforms such as Vercel or Cloudflare Workers. Supabase provides the managed Postgres database and authentication layer.
- **Payments:** Stripe is used by default but the `/pricing` API enables switching to local processors like PayPay or Line Pay with minimal code changes.
  Checkout sessions and webhooks update user entitlements automatically.
- **Analytics:** the `/analytics` endpoint logs anonymous events to a self-hosted solution, avoiding third-party trackers.

## Share image generation

When a quiz is completed the backend creates a branded result image using Pillow. The image is uploaded to the Supabase bucket defined by `SUPABASE_SHARE_BUCKET` and the public URL is returned alongside the score. The frontend sets Open Graph and Twitter meta tags with this URL so that shared links display the personalised card.

## Updating the normative distribution

IQ percentiles rely on `backend/data/normative_distribution.json`. Trigger the `/admin/update-norms` endpoint weekly with `ADMIN_API_KEY` to append recent scores and keep only the latest 5000 values.

Screenshots of the new design can be found under [docs/screenshots](docs/screenshots/).
