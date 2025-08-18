import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import SurveyStatsCard from '../components/SurveyStatsCard';
import { apiGet } from '../api';
import { supabase } from '../lib/supabaseClient';

export default function Arena() {
  const [cards, setCards] = useState([]);

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
      const arr = [];
      for (const s of list) {
        try {
          const st = await apiGet(`/stats/surveys/${s.id}/iq_by_option`);
          arr.push({ id: s.id, title: st.survey_title, items: st.items });
        } catch {
          /* ignore */
        }
      }
      setCards(arr);
    })();
  }, []);

  return (
    <AppShell>
      <div className="px-4 py-6">
        <h1 className="text-2xl font-bold mb-4">統計</h1>
        <div className="flex overflow-x-auto gap-4 snap-x snap-mandatory">
          {cards.map((c) => (
            <div key={c.id} className="snap-start">
              <SurveyStatsCard surveyId={c.id} surveyTitle={c.title} data={c.items} />
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
