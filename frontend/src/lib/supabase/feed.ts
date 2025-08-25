import type { SupabaseClient } from '@supabase/supabase-js';
import type { SurveyFeedRow } from './rpc-types';
import type { Database } from './database.types';

function logRpcError(name: string, error: unknown): void {
  const payload = {
    name,
    message: error instanceof Error ? error.message : String(error),
  };
  try {
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      navigator.sendBeacon('/api/telemetry', JSON.stringify(payload));
    }
  } catch {
    /* ignore */
  }
  // eslint-disable-next-line no-console
  console.error(name, error);
}

export async function fetchSurveyFeed(
  supabase: SupabaseClient<Database>,
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
  if (error) {
    logRpcError('surveys_feed_for_me', error);
    throw error;
  }
  return data ?? [];
}

export async function hasAnsweredToday(
  supabase: SupabaseClient<Database>
): Promise<boolean> {
  const { data, error } = await supabase.rpc<boolean>('me_has_answered_today');
  if (error) {
    logRpcError('me_has_answered_today', error);
    throw error;
  }
  return data === true;
}

export async function creditPoints(
  supabase: SupabaseClient<Database>,
  userId: string,
  delta: number,
  reason: string,
  meta: unknown
): Promise<void> {
  const { error } = await supabase.rpc('credit_points', {
    p_user_id: userId,
    p_delta: delta,
    p_reason: reason,
    p_meta: meta,
  });
  if (error) {
    logRpcError('credit_points', error);
    throw error;
  }
}

export async function spendPoint(
  supabase: SupabaseClient<Database>,
  userId: string,
  reason: string,
  meta: unknown
): Promise<boolean> {
  const { data, error } = await supabase.rpc<boolean>('spend_point', {
    p_user_id: userId,
    p_reason: reason,
    p_meta: meta,
  });
  if (error) {
    logRpcError('spend_point', error);
    throw error;
  }
  return !!data;
}
