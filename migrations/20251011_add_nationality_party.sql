ALTER TABLE users ADD COLUMN IF NOT EXISTS nationality text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS party_log jsonb[];
ALTER TABLE parties ADD COLUMN IF NOT EXISTS country_code text;
