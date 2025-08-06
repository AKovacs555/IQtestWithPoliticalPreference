# Importing IQ Test Questions

Question files can be version controlled in the repository under `tests/questions/`.  Each JSON file must contain an array of objects using the following structure:

```json
[
  {
    "id": 0,
    "group_id": "uuid-string",
    "language": "ja",
    "question": "質問文",
    "options": ["A1", "A2", "A3", "A4"],
    "answer": 2,
    "irt_a": 1.0,
    "irt_b": 0.0,
    "image_prompt": null,
    "image": null
  }
]
```

## Importing into Supabase

Run the helper script to load all JSON files into the `questions` table:

```bash
python tools/import_questions.py --dir tests/questions
```

The script uses environment variables for Supabase authentication and will fail if they are missing.

## Required Environment Variables

| Variable | Purpose |
| --- | --- |
| `SUPABASE_URL` | URL of the Supabase project |
| `SUPABASE_API_KEY` | Service role or API key used by the backend |
| `VITE_API_BASE` | Base URL of the backend API for the React frontend |

Ensure these are set when running locally or in deployment so the admin panel and import script can access Supabase correctly.
