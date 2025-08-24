import { apiClient } from './lib/apiClient';

export const apiGet = apiClient.get;
export const apiPost = apiClient.post;
export const apiDelete = apiClient.delete;

export async function getProfile() {
  return apiGet('/user/profile');
}

export async function updateProfile(data: unknown) {
  return apiPost('/user/profile', data);
}

export async function getQuizStart(lang?: string | null, setId?: string | null) {
  let url = '/quiz/start';
  const params = new URLSearchParams();
  if (lang) params.set('lang', lang);
  if (setId) params.set('set_id', setId);
  if (Array.from(params).length) url += `?${params.toString()}`;
  return apiGet(url);
}

export async function getAttemptQuestions(attemptId: string) {
  return apiGet(`/quiz/attempts/${attemptId}/questions`);
}

export async function submitQuiz(attemptId: string, answers: unknown, surveys?: unknown) {
  return apiPost('/quiz/submit', { attempt_id: attemptId, answers, surveys });
}

export async function abandonQuiz(attemptId: string) {
  try {
    await apiPost('/quiz/abandon', { attempt_id: attemptId });
  } catch {
    // ignore
  }
}

export async function getAvailableSurveys(lang: string, country: string) {
  const params = new URLSearchParams({ lang, country });
  return apiGet(`/surveys/available?${params.toString()}`);
}

export async function respondSurvey(
  surveyId: string,
  optionIds: string[],
  otherTexts: Record<string, string>
) {
  return apiPost(`/surveys/${surveyId}/respond`, {
    option_ids: optionIds,
    other_texts: otherTexts,
  });
}

export async function getSurveyStats(surveyId: string) {
  return apiGet(`/surveys/${surveyId}/stats`);
}

// Legacy wrappers ---------------------------------------------------------
export async function getSurvey(lang?: string | null, userId?: string | null, nationality?: string | null) {
  const list = await getAvailableSurveys(lang || 'en', nationality || '');
  return { items: list } as any;
}

export async function submitSurvey(answers: unknown, userId?: string | null) {
  return {} as any;
}

export async function completeSurvey(userId?: string | null) {
  return {} as any;
}

export async function setNationality(userId: string, nationality: string) {
  return apiPost('/user/nationality', { user_id: userId, nationality });
}
