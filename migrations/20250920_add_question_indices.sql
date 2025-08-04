-- Add indexes for efficient question filtering
CREATE INDEX IF NOT EXISTS idx_questions_lang ON questions (lang);
CREATE INDEX IF NOT EXISTS idx_questions_approved ON questions (approved);
CREATE INDEX IF NOT EXISTS idx_questions_irt_b ON questions (irt_b);
