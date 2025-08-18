-- RPC to list surveys with at least one answer
create or replace function public.surveys_with_any_answers()
returns table(id uuid)
language sql
stable
as $$
    select distinct survey_id as id
    from public.survey_answers
    where survey_id is not null;
$$;
