ALTER TABLE public.users ADD COLUMN IF NOT EXISTS survey_completed boolean DEFAULT false;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS nationality text;
ALTER TABLE public.surveys ADD COLUMN IF NOT EXISTS target_countries jsonb DEFAULT '[]'::jsonb;
