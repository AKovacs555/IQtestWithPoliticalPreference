export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json }
  | Json[];

export type Database = {
  public: {
    Functions: {
      surveys_feed_for_me: {
        Args: { p_lang: string | null; p_limit: number; p_offset: number };
        Returns: {
          id: string;
          group_id: string;
          question_text: string;
          options: Json;
          lang: string;
          created_at: string;
          respondents: number;
          answered_by_me: boolean;
        }[];
      };
      me_has_answered_today: {
        Args: Record<string, never>;
        Returns: boolean;
      };
      credit_points: {
        Args: {
          p_user_id: string;
          p_delta: number;
          p_reason: string;
          p_meta: Json;
        };
        Returns: unknown;
      };
      spend_point: {
        Args: {
          p_user_id: string;
          p_reason: string;
          p_meta: Json;
        };
        Returns: boolean;
      };
    };
  };
};
