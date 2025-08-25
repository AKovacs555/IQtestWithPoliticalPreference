import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import SurveyStatsCard from './SurveyStatsCard';
import { apiGet, fetchSurveyFeed } from '../api';
import { supabase } from '../lib/supabaseClient';
import { useTranslation } from 'react-i18next';

export default function StatisticsBanner() {
  const [card, setCard] = useState(null);
  const { i18n } = useTranslation();

  useEffect(() => {
    (async () => {
      try {
        const list = await fetchSurveyFeed(supabase, i18n.language ?? null, 50, 0);
        if (!list?.length) return;
        const pick = list[Math.floor(Math.random() * list.length)];
        const st = await apiGet(`/stats/surveys/${pick.id}/iq_by_option`);
        setCard({ id: pick.id, title: st.survey_title, questionText: st.survey_question_text, items: st.items });
      } catch (err) {
        console.error('Failed to load survey stats', err);
      }
    })();
  }, [i18n.language]);

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
          <SurveyStatsCard surveyId={card.id} surveyTitle={card.title} surveyQuestion={card.questionText} data={card.items} />
        </div>
      )}
    </div>
  );
}
