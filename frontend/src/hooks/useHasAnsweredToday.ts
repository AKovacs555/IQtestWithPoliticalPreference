import type { SupabaseClient } from '@supabase/supabase-js';
import { hasAnsweredToday } from '../lib/supabase/feed';

export async function useHasAnsweredToday(supabase: SupabaseClient) {
  return await hasAnsweredToday(supabase);
}
