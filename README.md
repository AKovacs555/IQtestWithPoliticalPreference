# IQtestWithPoliticalPreference

This is a small Flask web application that presents a short IQ quiz followed by a political preference survey. Responses are stored anonymously and aggregated for a summary view.

## Setup

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application with:

```bash
python app.py
```

To seed the default questions into the database, run:

```bash
python manage.py
```

Environment variables:

- `SECRET_KEY` – Flask secret key (default `devkey`).
- `DATABASE_URL` – SQLAlchemy database URI (default uses a local SQLite file).
- `FLASK_DEBUG` – set to `1` to enable debug mode.
- `ENABLE_ANALYTICS` – set to `1` to include the optional analytics snippet.
- `ENABLE_ADS` – set to `1` to include ad scripts.
- `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY` – Stripe credentials for premium payments.

When deploying to a platform like Heroku or Render, set these environment variables along with `DATABASE_URL` and `SECRET_KEY`. Ensure HTTPS is enabled and cookies are sent securely.

The quiz is for entertainment/research purposes only and does **not** collect any personal information beyond the IQ score and selected party. No IP addresses are logged.

