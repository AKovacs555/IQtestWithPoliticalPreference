// Types for Supabase RPC responses
export type SurveyFeedRow = {
  id: string;
  group_id: string;
  question_text: string;
  options: unknown;
  lang: string;
  created_at: string;
  respondents: number;
  answered_by_me: boolean;
};
