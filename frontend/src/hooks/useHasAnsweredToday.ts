import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { hasAnsweredToday as rpcHasAnsweredToday } from '../lib/supabase/feed';

export function useHasAnsweredToday() {
  const [answeredToday, setAnsweredToday] = useState<boolean | null>(null);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    rpcHasAnsweredToday(supabase)
      .then(setAnsweredToday)
      .catch((e) => setError(e));
  }, []);

  return { answeredToday, error };
}
