# IQtestWithPoliticalPreference

This project provides an IQ quiz and political preference survey using a responsive freemium design. Older Flask implementations are stored in the `archive/` directory for reference while the active codebase runs on **FastAPI** with a **React** front end. The UI uses **Material UI** components with Tailwind utilities and works on mobile and desktop devices.

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
  - `SUPABASE_API_KEY` – API key for Supabase.
  - `SUPABASE_URL` – base URL for Supabase (required for share images).
  - The backend communicates with Supabase purely through the REST API so
    no `DATABASE_URL` is needed.
  - `SMS_PROVIDER` – `twilio` (default) or `sns` for Amazon SNS.
  - When using Twilio: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_VERIFY_SERVICE_SID`.
  - When using SNS: `AWS_REGION` and AWS credentials configured in the environment.
  - The backend logs an estimated cost for each OTP sent based on the selected SMS provider.
  - `NOWPAYMENTS_API_KEY` – API key for cryptocurrency payments.
  - `NOWPAYMENTS_CALLBACK_URL` – URL for payment confirmations.
  - `NOWPAYMENTS_CURRENCY` – fiat currency to convert payouts into (optional).
  - `PHONE_SALT` – salt for hashing phone or email identifiers.
  - `MAX_FREE_ATTEMPTS` – number of free quiz attempts allowed before payment is required (default `1`).
  - `RETRY_PRICE_TIERS` – comma separated yen prices for paid retries.
  - `PRO_PRICE_MONTHLY` – monthly cost of the optional subscription.
  - `DP_EPSILON` – epsilon used when adding Laplace noise to aggregated data.
  - `DP_MIN_COUNT` – minimum records required before an aggregate is reported.
  - `DATA_API_KEY` – authentication token for the paid differential‑privacy API.
  - `SUPABASE_SHARE_BUCKET` – bucket name for storing generated share images.
  - `ADMIN_API_KEY` – token for admin endpoints such as normative updates.
  - `AD_UNIT_ID_ANDROID`, `AD_UNIT_ID_IOS`, `ADMOB_APP_ID` – Google AdMob ad identifiers.
  - `AD_REWARD_POINTS` – points awarded per ad view.
  - `RETRY_POINT_COST` – points required for an extra attempt.
  - `VITE_API_BASE` – base URL of the backend API for the React app.
    This should point to the Render deployment, e.g.
    `https://iqandpoliticalpreference.onrender.com`. Be sure to redeploy
    the frontend after changing environment variables.

When running the project locally, copy `.env.example` to `.env` and fill in the
required keys before starting the backend or frontend.

## 環境設定

Supabase、NOWPayments、AWS SNS、Google AdMob のアカウントを作成し、それぞれのダッシュボードから API キーを取得してください。取得したキーは Vercel または Render の環境変数に設定します。

- [Supabase ドキュメント](https://supabase.com/docs)
- [NOWPayments ドキュメント](https://nowpayments.io)
- [AWS SNS ドキュメント](https://docs.aws.amazon.com/sns)
- [Google AdMob ドキュメント](https://developers.google.com/admob)

- Supabase: Settings > API で URL と service role キーをコピー
- NOWPayments: 個人商人アカウントを作成し、API キーを生成してコールバック URL を設定
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
- Quiz endpoints: `/quiz/sets` returns the list of available set IDs. `/quiz/start?set_id=<id>` begins a quiz and provides a session ID along with the questions for that set. `/quiz/submit` accepts all answers at once and returns the score, percentile and share URL. `/adaptive/start` and `/adaptive/answer` remain for legacy clients but are no longer used by the default frontend.
- The quiz now samples questions by difficulty (30% easy, 40% medium, 30% hard) for a balanced test.
- Pricing endpoints: `/pricing/{id}` shows the dynamic price for a user, `/play/record` registers a completed play and `/referral` adds a referral credit.
- Demographic and party endpoints: `/user/demographics` records age, gender and income band. `/user/party` stores supported parties and enforces monthly change limits.
- Aggregated data is available via `/leaderboard` and the authenticated `/data/iq` endpoint which returns differentially private averages.
- Admins can bulk import questions by POSTing a JSON file to `/admin/import_questions` with the `X-Admin-Token` header. A newer endpoint `/admin/import_questions_with_images` also accepts image files and uploads them to Supabase Storage. Each item may include an `image_filename` referencing an uploaded file or a direct `image` URL.
- The web interface at `/#/admin/questions` offers a simple UI for this:
  1. Enter your `ADMIN_TOKEN` and click **Load Questions**.
  2. Select a JSON file and optional image files then click **Import Questions**. You can also edit/delete existing items.
- The question bank with psychometric metadata lives in `backend/data/question_bank.json`. Use `tools/generate_questions.py --import_dir=generated_questions` to merge question files you created with ChatGPT.
 - Individual question sets for the live quiz are stored under `questions/`. Each file must conform to `questions/schema.json` and can be fetched via `/quiz/start?set_id=set01`.
 - The backend reads these JSON files at runtime so new sets can be added via GitHub without redeploying the API. Non‑developers can simply upload a file like `set03.json` to the `questions/` folder using the web interface.
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

### Translating question sets

To localise a manually created test into other languages run:

```bash
python tools/translate_questions.py --input questions/set02_ja.json --languages en,tr,ru,zh
```

Set `OPENAI_API_KEY` before execution. Translated files such as `set02_en.json`
are written next to the source JSON.

## Frontend (React)

 - Located in `frontend/` and built with Vite, React Router, Tailwind CSS and Material UI components with framer‑motion.
- Install dependencies with `npm install` and start the dev server with `npm run dev`.
- The UI uses a responsive layout. The previous mobile restriction was removed and
  `MobileOnlyWrapper` now simply renders its children.
- Basic anti-cheat measures disable text selection, draw questions on a canvas
  and apply a watermark. Comments note that screenshots cannot be fully blocked.
- React components are organised under `src/components` and `src/pages` for clarity.
- The `Quiz` component now stores answers locally and submits them all at once via `/quiz/submit`.
- Each test session is limited to 5 minutes and will auto-submit when time runs out.
- A new `Leaderboard` page displays average IQ by party using the `/leaderboard` API.
- Users can toggle between light and dark themes using the button in the navbar.
- Translations live under `frontend/translations/` and are loaded via `src/i18n.js`.
  Vite's config enables JSON imports so new languages can be added without code changes.
- The landing page uses framer-motion for parallax scrolling and animated calls to action, while quiz pages feature progress bars and confetti on completion.

To get started quickly, deploy the backend and frontend separately.

### Deploying the backend on Render

1. Connect the repository and Render will read `render.yaml` automatically.
2. The service builds with `pip install -r requirements.txt` inside `backend/`.
3. It starts using `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
4. Set the required environment variables from the Render dashboard.

### Deploying the frontend on Vercel

1. Create a Vercel project and point it at the `frontend/` directory.
2. Define `VITE_API_BASE` and any Supabase keys under *Project Settings → Environment Variables*.
3. After configuring the variables run `vercel env pull` to generate a local `.env` file for development.
4. Use `npm install` followed by `npm run build` for the build steps.
5. Any change to the variables requires a redeploy from Vercel’s dashboard.

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
  Prices and retry tiers are controlled via `MAX_FREE_ATTEMPTS`,
  `RETRY_PRICE_TIERS` and `PRO_PRICE_MONTHLY` environment variables.  Aggregated
  insights are also available from the authenticated `/data/iq` endpoint.

## Points System

Users earn points by watching rewarded ads via `/ads/start` and `/ads/complete`.
The balance is returned from `/points/{user_id}` and `RETRY_POINT_COST` points
can substitute payment when calling `/play/record`. 1 point is granted per ad
view by default (`AD_REWARD_POINTS`).

## Question schema

Question sets in `questions/` follow `questions/schema.json` and contain the following fields:

- `id` (string): unique identifier for the set.
- `language` (string): ISO code such as `en` or `ja`.
- `title` (string): human‑readable title for the set.
- `questions` (array): list of objects with:
  * `id` (integer) – unique within the set (optional for automatic numbering).
  * `question` (string) – the question text.
  * `options` (array of strings) – four answer choices.
  * `answer` (integer) – zero‑based index (0–3) of the correct answer.
  * `irt` (object) – psychometric parameters `{ "a": 1.0, "b": 0.0 }` by default.
  * `image` (string, optional) – relative path to an image shown above the question.
  * `image_prompt` (string, optional) – description of the image for accessibility.

Older files using `text` and `correct_index` are still supported by the backend, but new files should adopt `question` and `answer`.
Files are validated against `questions/schema.json` at startup so new sets can be committed without redeploying the API.
To manually check your JSON before committing, run:
```bash
python tools/validate_questions.py
```

Place any image files referenced by the `image` field under
`frontend/public/images/questions/` (or another static asset path) so they
are served directly by the React app. Store the relative URL in the JSON,
for example `/images/questions/set01_q01.png`.

## Internationalisation

All strings reside under `frontend/translations/` and are loaded by
`src/i18n.js`. English and Japanese locales are provided. Add new languages by
creating a JSON file in that folder and updating `i18n.js`. The UI supports RTL
languages using the `dir` attribute on the root element.

## Services and Costs

- **SMS verification:** configurable between Twilio and Amazon SNS. Choose the provider with the best local rates.
- **Email OTP:** provided free via Supabase auth as a fallback for users without SMS.
- **Serverless hosting:** deploy FastAPI on platforms such as Vercel or Cloudflare Workers. Supabase provides the managed Postgres database and authentication layer.
- **Payments:** Cryptocurrency payments are handled via NOWPayments and PayPal can be used if credentials are provided.
  NOWPayments invoices support SOL, XRP, TRX, USDT, ETH and BNB.
- **Analytics:** the `/analytics` endpoint logs anonymous events to a self-hosted solution, avoiding third-party trackers.

## Share image generation

When a quiz is completed the backend creates a branded result image using Pillow. The image is uploaded to the Supabase bucket defined by `SUPABASE_SHARE_BUCKET` and the public URL is returned alongside the score. The frontend sets Open Graph and Twitter meta tags with this URL so that shared links display the personalised card.

## Updating the normative distribution

IQ percentiles rely on `backend/data/normative_distribution.json`. Trigger the `/admin/update-norms` endpoint weekly with `ADMIN_API_KEY` to append recent scores and keep only the latest 5000 values.

Screenshots of the new design can be found under [docs/screenshots](docs/screenshots/).
