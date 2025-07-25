import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
);

export interface Question {
  id: number;
  question: string;
  options: string[];
}

export async function fetchExam() {
  const { data, error } = await supabase.rpc("fetch_exam", {
    _easy: 9,
    _med: 12,
    _hard: 9,
  });
  if (error) throw error;
  return data as Question[];
}
