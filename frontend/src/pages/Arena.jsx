import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import SurveyStatsCard from '../components/SurveyStatsCard';
import { apiGet, fetchSurveyFeed } from '../api';
import { supabase } from '../lib/supabaseClient';
import { useTranslation } from 'react-i18next';

export default function Arena() {
  const [cards, setCards] = useState([]);
  const { i18n } = useTranslation();

  useEffect(() => {
    (async () => {
      try {
        const list = await fetchSurveyFeed(supabase, i18n.language ?? null, 50, 0);
        const arr = [];
        for (const s of list) {
          try {
            const st = await apiGet(`/stats/surveys/${s.id}/iq_by_option`);
            arr.push({ id: s.id, title: st.survey_title, questionText: st.survey_question_text, items: st.items });
          } catch (err) {
            console.error('Failed to fetch survey stats', err);
          }
        }
        setCards(arr);
      } catch (err) {
        console.error('Failed to fetch surveys', err);
      }
    })();
  }, [i18n.language]);

  return (
    <AppShell>
      <div className="px-4 py-6">
        <h1 className="text-2xl font-bold mb-4">統計</h1>
        {cards.length === 0 ? (
          <p className="text-gray-500">統計データが見つかりません</p>
        ) : (
          <div className="flex overflow-x-auto gap-4 snap-x snap-mandatory">
            {cards.map((c) => (
              <div key={c.id} className="snap-start">
                <SurveyStatsCard surveyId={c.id} surveyTitle={c.title} surveyQuestion={c.questionText} data={c.items} />
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
