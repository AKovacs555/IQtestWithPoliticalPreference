-- Phase 2 security and performance preparations.
-- These statements are provided for ops use and are NOT executed by default.

-- Remove redundant indexes
DROP INDEX IF EXISTS idx_survey_items_survey_id_duplicated;
DROP INDEX IF EXISTS idx_survey_answers_survey_id_duplicated;
DROP INDEX IF EXISTS idx_quiz_attempts_user_id_duplicated;

-- Add updated_at triggers
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS set_updated_at ON survey_items;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON survey_items
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON survey_answers;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON survey_answers
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON quiz_attempts;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON quiz_attempts
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Prepared (but disabled) RLS policies
-- ALTER TABLE survey_items ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "survey_items_owner" ON survey_items
--     USING (auth.uid() = user_id);

-- Storage policies will be added here in a future deployment.
