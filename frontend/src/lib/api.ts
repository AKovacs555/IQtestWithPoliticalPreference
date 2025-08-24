import { apiClient } from './apiClient';

export async function fetchProfile() {
  return apiClient.get('/user/profile');
}

export interface SurveyItemPayload {
  body: string;
  is_exclusive?: boolean;
  lang: string;
}

export interface SurveyPayload {
  title: string;
  question_text: string;
  type: 'sa' | 'ma';
  lang: string;
  target_countries: string[];
  target_genders: string[];
  items: SurveyItemPayload[];
}

export async function getSurveys() {
  return apiClient.get('/admin/surveys');
}

export async function updateSurveyStatus(id: string, payload: { status: string; is_active: boolean }) {
  return apiClient.post(`/admin/surveys/${id}/status`, payload);
}

export async function createSurvey(payload: SurveyPayload) {
  return apiClient.post('/admin/surveys', payload);
}

export async function updateSurvey(id: string, payload: SurveyPayload) {
  return apiClient.post(`/admin/surveys/${id}`, payload);
}

export async function deleteSurvey(id: string) {
  return apiClient.delete(`/admin/surveys/${id}`);
}

export async function getAvailableSurveys(lang: string, country: string) {
  return apiClient.get(`/surveys/available?lang=${encodeURIComponent(lang)}&country=${encodeURIComponent(country)}`);
}

export async function respondSurvey(
  surveyId: string,
  optionIds: string[],
  otherTexts: Record<string, string>
) {
  return apiClient.post(`/surveys/${surveyId}/respond`, { option_ids: optionIds, other_texts: otherTexts });
}

export async function getSurveyStats(surveyId: string) {
  return apiClient.get(`/surveys/${surveyId}/stats`);
}

export async function getAttemptQuestions(attemptId: string) {
  return apiClient.get(`/quiz/attempts/${attemptId}/questions`);
}
