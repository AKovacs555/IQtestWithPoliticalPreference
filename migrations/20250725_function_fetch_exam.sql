create or replace function fetch_exam(_easy int, _med int, _hard int)
returns setof jsonb
language sql as $$
  with e as (select body from iq_questions where bucket='easy' and is_active order by random() limit _easy),
       m as (select body from iq_questions where bucket='medium' and is_active order by random() limit _med),
       h as (select body from iq_questions where bucket='hard' and is_active order by random() limit _hard)
  select body from e union all select body from m union all select body from h order by random();
$$;
