import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { SearchForm, SearchResult } from './components';
import { searchApi, getJobStatus, getContentApi, getAnalyticsSummary } from './services/api';
import type { SearchResponse, JobStatus, ContentResult, AnalyticsSummary } from './types';

function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [submittedQuery, setSubmittedQuery] = useState('');

  const searchMutation = useMutation<SearchResponse, unknown, { query: string }>({
    mutationFn: (payload) => searchApi(payload),
    onSuccess: (data) => {
      setJobId(data.job_id);
      setSubmittedQuery(data.query);
    },
  });

  const statusQuery = useQuery<JobStatus, unknown>({
    queryKey: ['job-status', jobId ?? ''],
    queryFn: () => getJobStatus(jobId as string),
    enabled: Boolean(jobId),
    refetchInterval: 2000,
  });

  const contentQuery = useQuery<ContentResult>({
    queryKey: ['content', submittedQuery],
    queryFn: () => getContentApi(submittedQuery),
    enabled: Boolean(submittedQuery) && statusQuery.data?.progress_pct === 100,
  });

  const analyticsQuery = useQuery<AnalyticsSummary>({
    queryKey: ['analytics', submittedQuery],
    queryFn: () => getAnalyticsSummary(submittedQuery),
    enabled: Boolean(submittedQuery) && statusQuery.data?.progress_pct === 100,
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-6xl px-4 py-8">
        <header className="mb-10 text-center">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-400">Brand Intelligence Engine</p>
          <h1 className="mt-4 text-4xl font-semibold">Search, analyze, and review brand content.</h1>
          <p className="mt-3 text-slate-400">Submit a query to ingest search results, then review processed content and analytics.</p>
        </header>

        <SearchForm
          isLoading={searchMutation.isPending}
          onSubmit={(value) => {
            searchMutation.mutate({ query: value });
          }}
        />

        {searchMutation.data && (
          <div className="mt-6 rounded-3xl border border-slate-800 bg-slate-900/80 p-5">
            <p className="text-sm text-slate-400">Search submitted for</p>
            <p className="mt-1 text-lg text-white">{searchMutation.data.query}</p>
            <p className="text-sm text-slate-400">Job ID: {searchMutation.data.job_id}</p>
          </div>
        )}

        {statusQuery.data && (
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <StatusCard label="Progress" value={`${statusQuery.data.progress_pct}%`} />
            <StatusCard label="Completed" value={`${statusQuery.data.completed}`} />
            <StatusCard label="Pending" value={`${statusQuery.data.pending}`} />
          </div>
        )}

        {contentQuery.data && (
          <section className="mt-10 space-y-6">
            <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
              <h2 className="text-xl font-semibold">Top matched documents</h2>
              <p className="mt-2 text-sm text-slate-400">{contentQuery.data.total} results for "{contentQuery.data.query}"</p>
              <div className="mt-4 space-y-4">
                {(contentQuery.data.results ?? []).slice(0, 6).map((item) => (
                  <SearchResult key={item.url_hash} item={item} />
                ))}
              </div>
            </div>
          </section>
        )}

        {analyticsQuery.data && (
          <section className="mt-10 grid gap-6 lg:grid-cols-2">
            <AnalyticsPanel data={analyticsQuery.data} />
          </section>
        )}
      </div>
    </div>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

function AnalyticsPanel({ data }: { data: { query: string; total_documents: number; unique_domains: number; avg_relevance: number; avg_confidence: number; top_domains: string[] } }) {
  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/80 p-6">
      <h2 className="text-xl font-semibold">Analytics summary</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Stat label="Total docs" value={`${data.total_documents}`} />
        <Stat label="Unique domains" value={`${data.unique_domains}`} />
        <Stat label="Avg relevance" value={`${data.avg_relevance}`} />
        <Stat label="Avg confidence" value={`${data.avg_confidence}`} />
      </div>
      <div className="mt-6">
        <p className="text-sm text-slate-400">Top domains</p>
        <ul className="mt-3 space-y-2 text-sm text-slate-200">
          {(data.top_domains ?? []).map((domain) => (
            <li key={domain} className="rounded-2xl bg-slate-950/80 px-4 py-3">{domain}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-3xl bg-slate-950/80 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

export default App;
