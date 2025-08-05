ALTER TABLE questions
  ADD COLUMN IF NOT EXISTS image text,
  ADD COLUMN IF NOT EXISTS option_images text[];
