import type { SupabaseClient } from '@supabase/supabase-js';
import type { SurveyFeedRow } from './rpc-types';

export async function fetchSurveyFeed(
  supabase: SupabaseClient,
  lang: string | null,
  limit = 50,
  offset = 0
): Promise<SurveyFeedRow[]> {
  const { data, error } = await supabase
    .rpc<SurveyFeedRow[]>('surveys_feed_for_me', {
      p_lang: lang ?? null,
      p_limit: limit,
      p_offset: offset
    });
  if (error) throw error;
  return data ?? [];
}

export async function hasAnsweredToday(
  supabase: SupabaseClient
): Promise<boolean> {
  const { data, error } = await supabase.rpc<boolean>('me_has_answered_today');
  if (error) throw error;
  return data === true;
}
