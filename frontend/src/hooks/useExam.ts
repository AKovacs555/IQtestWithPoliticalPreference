import { createClient } from "@supabase/supabase-js";

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      flowType: "pkce", // ブラウザでも PKCE を明示
    },
  }
);

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
