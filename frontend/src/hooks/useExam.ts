import { supabase } from "../lib/supabaseClient";
export { supabase };

export interface Question {
  id: number;
  question: string;
  options: string[];
  image?: string;
  option_images?: string[];
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
