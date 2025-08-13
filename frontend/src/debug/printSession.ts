import { supabase } from '../lib/supabaseClient';

export async function printSession() {
  const { data } = await supabase.auth.getSession();
  // eslint-disable-next-line no-console
  console.log('[session]', data.session?.user?.app_metadata);
}
