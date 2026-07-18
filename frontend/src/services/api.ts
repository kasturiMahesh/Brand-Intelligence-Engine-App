import axios from 'axios';
import type { SearchResponse, ContentResult, AnalyticsSummary, JobStatus } from '../types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function searchApi({ query }: { query: string }): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>('/api/v1/search/', {
    query,
    max_results: 30,
  });
  return response.data;
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await api.get<JobStatus>(`/api/v1/search/status/${jobId}`);
  return response.data;
}

export async function getContentApi(query: string): Promise<ContentResult> {
  const response = await api.get<ContentResult>('/api/v1/content/', {
    params: { query, min_relevance: 0.4, limit: 12 },
  });
  return response.data;
}

export async function getAnalyticsSummary(query: string): Promise<AnalyticsSummary> {
  const response = await api.get<AnalyticsSummary>('/api/v1/analytics/summary', {
    params: { query },
  });
  return response.data;
}
