# IQ Arena Frontend Final Blueprint

This document consolidates the final frontend/UI and product requirements for IQ Arena, merging functionality from the existing implementation (A) with the design principles of repository B.

## 0. Immutable Principles
- **Daily 3 Required**: Users must answer three daily poll questions to unlock testing for that day.
- **Test Fairness**: Once a test starts, timeout or tab leave forces submission; unanswered items are treated as incorrect (no penalty).
- **Public Aggregation**: Option statistics are published with differential privacy and hidden for small counts.
- **Admin Exposure**: The `Admin` tab appears only when `is_admin=true` with triple (UI, route, API) guarding.
- **Social Sharing**: Default posts append official hashtags like `#IQArena`.
- **Monetization**: Freemium model with ads, one‑off purchases, Pro subscriptions, and paid polls.
- **Legal**: Prohibit illegal, defamatory, privacy‑violating, discriminatory, or personal‑data content. Review SLA = 48h.

## 1. Global UI Framework
- Sticky header with logo link and nav items (Home, Dashboard, Test, Results, Admin, Profile).
- Status pills show `Daily 3: x/3`, `Free tries`, and `Pro` state.
- Mobile uses hamburger drawer, desktop shows tabs. Built with MUI + Tailwind.
- Global toasts, modals, accessibility, and i18n (en/ja).

## 2. Screen‑Specific UX
### Home
- Hero: "毎日3問で、すぐ測れる" with CTA depending on Daily 3 completion.
- Value propositions and carousel of trending polls.
### Auth
- Google login (One Tap optional); error messages `auth/error_generic` and `auth/error_blocked`.
### Dashboard
- Cards for Daily 3 progress, remaining attempts with ad/purchase/Pro actions, Pro status, history with detail modal, invite progress, and poll submission queue with 48h review timer.
### Daily 3 Polls
- Random unanswered items; 1‑tap answers; stepper; completion confetti and "IQテストへ" button; locked after 3/3 until midnight.
### Test
- Entry gate ensures Daily 3 and attempts/Pro access.
- Session: server `attempt_id`, server timer.
- UI with timer, progress bar, single‑choice answers (1‑5 hotkeys), Next and Exit buttons.
- Tab leave or refresh warns then forces finish; scoring uses IRT.
### Results
- Summary: score, deviation, percentile.
- Comparison to history and aggregated stats (DP).
- Share button with hashtags and OG image.
- Retry button leading to purchase/ads if no attempts remain.
### Admin
- Tabs: Review, Pricing, Invite limits, Difficulty coverage, Reports.
- Review UI checks legality/privacy/discrimination; approve publishes & charges immediately.
- Reports show Daily 3 completion, test completion, ad SSV failures, payment success, ARPU.

## 3. Monetization & Ads
- One‑off purchases via PayPal or NOWPayments; webhooks grant attempts idempotently.
- Pro subscription via PayPal Subscriptions with webhook lifecycle.
- Rewarded ads grant attempts after server‑side verification; daily limits and cooldowns.

## 4. Poll Submission Flow
- Form with title, purpose, questions, budget, targeting, expected responses, duration, and consent checks.
- Admin approval enforces content policy; approval triggers automatic charging and publishing.

## 5. Data & API Overview
- Key tables: users, daily_counters, attempts, attempt_ledger, polls, pricing_country, subscriptions, payments, ad_events, share_assets, aggregates.
- Representative endpoints: polls/daily, quiz/session/start & finish, payments, subscriptions, ads reward callback, admin endpoints.

## 6. Telemetry
- North Star: monthly tests per user.
- Events include daily3_completed, quiz_started, quiz_forced_finish, result_viewed, share_clicked, ad_reward_verified, purchase_succeeded, subscription_activated, poll_submitted, poll_approved.
- KPIs: ARPU, payment conversion, ad eCPM, Daily 3 completion rate, test completion rate, share rate, invite K factor.

## 7. Security & Privacy
- Differential privacy parameters (e.g., ε=1.0, min_count=50).
- Anti‑fraud: multi‑account, self‑referral, fake SSV; block via rate limiting and device fingerprint.
- Data minimization with hashed identifiers and support for export/delete requests.

## 8. Sample Messages
- Daily 3 incomplete, leave warning, payment success, SSV failure, etc.

## 9. 3‑Day Launch Plan
- Day1: Admin exposure, Daily 3 API/UI, test gate.
- Day2: Forced finish, PayPal purchase flow, SSV endpoint, result sharing.
- Day3: Pro subscription, DP min_count, public smoke test.

## 10. Acceptance Criteria
- `/quiz/session/start` returns 403 before Daily 3 completion; afterwards poll UI hidden.
- Forced finish on timeout/leave with results page.
- Payments grant attempts with idempotent webhooks.
- Ads grant attempts only when SSV verified respecting limits.
- Share default hashtags.
- Admin tab/routes/API accessible only when `is_admin=true`.
- Aggregates hide partitions below min_count.

