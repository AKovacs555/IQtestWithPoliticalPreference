create or replace function fetch_exam(_easy int, _med int, _hard int)
returns setof questions as $$
begin
  return query (
    select id, question, options, answer, irt_a, irt_b, image
      from questions where irt_b <= -0.33 order by random() limit _easy
  )
  union all
  select id, question, options, answer, irt_a, irt_b, image
    from questions where irt_b > -0.33 and irt_b < 0.33 order by random() limit _med
  union all
  select id, question, options, answer, irt_a, irt_b, image
    from questions where irt_b >= 0.33 order by random() limit _hard;
end;
$$ language plpgsql;
