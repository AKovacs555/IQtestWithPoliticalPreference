CREATE TABLE IF NOT EXISTS public.user_scores (
  id serial PRIMARY KEY,
  user_id text,
  session_id text,
  iq numeric,
  percentile numeric,
  created_at timestamptz DEFAULT timezone('utc', now())
);
