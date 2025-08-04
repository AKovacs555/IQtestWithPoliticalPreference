CREATE TABLE IF NOT EXISTS public.survey_responses (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id text NOT NULL,
  survey_group_id uuid NOT NULL,
  answer jsonb NOT NULL,
  created_at timestamp with time zone DEFAULT timezone('utc', now())
);
