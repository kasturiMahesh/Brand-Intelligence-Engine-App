export interface SearchResponse {
  job_id: string;
  query: string;
  urls_found: number;
  queued: number;
  message: string;
}

export interface JobStatus {
  job_id: string;
  query: string;
  total_urls: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  skipped: number;
  progress_pct: number;
}

export interface ContentItem {
  url: string;
  url_hash: string;
  query: string;
  source_domain: string;
  title: string;
  meta_description: string;
  headings: {
    h1: string[];
    h2: string[];
    h3: string[];
  };
  content_summary: string;
  key_points: string[];
  relevance_score: number;
  confidence_score: number;
  sentiment: string;
  source_credibility: string;
  word_count: number;
  language: string;
  timestamp: string;
}

export interface ContentResult {
  query: string;
  total: number;
  returned: number;
  page: number;
  results: ContentItem[];
}

export interface AnalyticsSummary {
  query: string;
  total_documents: number;
  unique_domains: number;
  avg_relevance: number;
  avg_confidence: number;
  avg_word_count?: number;
  total_words?: number;
  sentiment?: Record<string, number>;
  source_credibility?: Record<string, number>;
  languages?: Record<string, number>;
  top_domains: string[];
}
