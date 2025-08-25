#!/bin/sh
# Refresh materialized views for v2 statistics.
set -e
psql "$DATABASE_URL" <<'SQL'
REFRESH MATERIALIZED VIEW CONCURRENTLY survey_choice_iq_stats_v2;
REFRESH MATERIALIZED VIEW CONCURRENTLY survey_group_choice_iq_stats_v2;
REFRESH MATERIALIZED VIEW CONCURRENTLY user_best_iq_unified_v2;
SQL
