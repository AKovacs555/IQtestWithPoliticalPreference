import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import SurveyStatsCard from '../components/SurveyStatsCard';
import { apiGet } from '../api';

export default function Arena() {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    apiGet('/stats/surveys/with_data')
      .then(async (list) => {
        const arr = [];
        for (const s of list) {
          const st = await apiGet(`/stats/surveys/${s.id}/iq_by_option`);
          arr.push({ id: s.id, title: st.survey_title, items: st.items });
        }
        setCards(arr);
      })
      .catch(() => setCards([]));
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
