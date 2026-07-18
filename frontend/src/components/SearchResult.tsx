import { ChevronRight } from 'lucide-react';
import type { ContentItem } from '../types';

export default function SearchResult({ item }: { item: ContentItem }) {
  return (
    <article className="rounded-3xl border border-slate-800 bg-slate-900/80 p-5 shadow-lg shadow-slate-950/20">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">{item.source_domain}</p>
          <h3 className="text-lg font-semibold text-white">{item.title || item.url}</h3>
        </div>
        <span className="rounded-full bg-slate-950/70 px-3 py-1 text-xs uppercase tracking-[0.24em] text-slate-400">{item.sentiment}</span>
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-300">{item.content_summary}</p>

      <div className="mt-5 grid gap-2 sm:grid-cols-3">
        <Stat label="Relevance" value={item.relevance_score.toFixed(2)} />
        <Stat label="Confidence" value={item.confidence_score.toFixed(2)} />
        <Stat label="Words" value={item.word_count.toString()} />
      </div>

      <div className="mt-5 flex items-center justify-between text-sm text-slate-400">
        <a
          href={item.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-2 text-sky-300 hover:text-sky-200"
        >
          Open source
          <ChevronRight size={16} />
        </a>
      </div>
    </article>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-slate-950/70 px-4 py-3 text-sm">
      <p className="text-slate-500">{label}</p>
      <p className="mt-1 font-semibold text-white">{value}</p>
    </div>
  );
}
