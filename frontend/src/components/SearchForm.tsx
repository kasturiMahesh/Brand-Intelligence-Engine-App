import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';

interface FormValues {
  query: string;
}

interface Props {
  isLoading: boolean;
  onSubmit: (query: string) => void;
}

export default function SearchForm({ isLoading, onSubmit }: Props) {
  const { register, handleSubmit, reset } = useForm<FormValues>({
    defaultValues: { query: '' },
  });

  return (
    <form
      onSubmit={handleSubmit((values) => {
        if (!values.query.trim()) {
          toast.error('Please enter a search query.');
          return;
        }
        onSubmit(values.query.trim());
        reset({ query: '' });
      })}
      className="rounded-3xl border border-slate-800 bg-slate-900/90 p-6 shadow-xl shadow-slate-950/30"
    >
      <label className="block text-sm font-medium text-slate-200">Brand query</label>
      <div className="mt-3 flex flex-col gap-3 sm:flex-row">
        <input
          type="text"
          placeholder="e.g. Amazon customer trust 2026"
          className="min-w-0 flex-1 rounded-2xl border border-slate-700 bg-slate-950/80 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
          {...register('query', { required: true, minLength: 2 })}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center justify-center rounded-2xl bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-sky-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isLoading ? 'Searching…' : 'Run search'}
        </button>
      </div>
    </form>
  );
}
