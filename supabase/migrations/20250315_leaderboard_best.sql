drop view if exists leaderboard_best;
create view leaderboard_best as
select user_id,
       max(iq_score) as best_iq,
       max(coalesce(percentile,0)) as best_percentile
from quiz_attempts qa
where qa.status in ('submitted','timeout','abandoned')
group by user_id;
