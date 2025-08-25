import type { SupabaseClient } from '@supabase/supabase-js';

export async function refreshAnalytics(supabase: SupabaseClient): Promise<void> {
  const { error } = await supabase.rpc('refresh_analytics');
  if (error) throw error;
}

