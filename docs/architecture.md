# Project Architecture

```
backend/
  main.py          - FastAPI application
  questions.py     - Question set loader
  tests/           - API unit tests

frontend/
  src/
    components/    - Reusable UI components
    pages/         - Route level pages
    hooks/         - Custom hooks
    store/         - Zustand global state
    utils/         - Helper functions
```

Question sets live under the root `questions/` directory and are loaded at runtime by the backend.
