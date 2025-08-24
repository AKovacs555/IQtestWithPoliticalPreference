# V2 Cutover Playbook

This document outlines how to switch read-only stats to the new v2 materialized views.

## Enable v2 views

1. Set environment variable `USE_V2_STATS=true` on the backend.
2. Redeploy the backend service.

## Refresh materialized views

Run `scripts/refresh_materialized_views.sh` after large data imports or before cutover:

```sh
scripts/refresh_materialized_views.sh
```

## Rollback

1. Set `USE_V2_STATS=false`.
2. Redeploy the backend.
3. No further action is required; legacy views remain intact.

## Notes

RLS and storage policy updates are staged in `supabase/sql/phase2_policies.sql` but are not enabled by default.
