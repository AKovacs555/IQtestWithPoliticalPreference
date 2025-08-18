import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SurveyStatsCard from './SurveyStatsCard';
import { apiGet } from '../api';
import { supabase } from '../lib/supabaseClient';

export default function StatisticsBanner() {
  const [card, setCard] = useState(null);

  useEffect(() => {
    (async () => {
      let list = [];
      try {
        list = await apiGet('/stats/surveys/with_data');
      } catch {
        const { data } = await supabase
          .from('survey_answers')
          .select('survey_id');
        const ids = Array.from(new Set((data || []).map(r => r.survey_id).filter(Boolean)));
        list = ids.map(id => ({ id }));
      }
      if (!list?.length) return;
      const pick = list[Math.floor(Math.random() * list.length)];
      try {
        const st = await apiGet(`/stats/surveys/${pick.id}/iq_by_option`);
        setCard({ id: pick.id, title: st.survey_title, items: st.items });
      } catch {
        /* ignore */
      }
    })();
  }, []);

  return (
    <div className="mb-4 rounded-2xl p-4 bg-gradient-to-r from-cyan-600/40 to-emerald-600/40">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">統計</h2>
        <Link to="/arena" className="px-3 py-1 rounded bg-white/10 hover:bg-white/20">
          統計へ
        </Link>
      </div>
      {card && (
        <div className="mt-3">
          <SurveyStatsCard surveyId={card.id} surveyTitle={card.title} data={card.items} />
        </div>
      )}
    </div>
  );
}
