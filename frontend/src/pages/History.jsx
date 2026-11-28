import { useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { LENGTH_LABELS } from '../constants/summarization';
import {
  clearHistory,
  deleteHistoryItem,
  getHistory,
} from '../services/history';

function formatTimestamp(isoString) {
  try {
    return new Date(isoString).toLocaleString();
  } catch {
    return isoString || '';
  }
}

function History() {
  const navigate = useNavigate();
  const [items, setItems] = useState(() => getHistory());
  const [query, setQuery] = useState('');
  const [confirmClear, setConfirmClear] = useState(false);

  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return items;
    return items.filter(
      (item) =>
        item.sourceName?.toLowerCase().includes(q) ||
        item.result?.extractive_summary?.toLowerCase().includes(q)
    );
  }, [items, query]);

  const handleOpenResult = (item) => {
    navigate('/results', {
      state: {
        result: item.result,
        summaryLength: item.summaryLength,
        sourceType: item.sourceType,
        sourceName: item.sourceName,
        claims: item.claims || [],
        historyId: item.id,
        createdAt: item.createdAt,
      },
    });
  };

  const handleDelete = (id) => {
    setItems(deleteHistoryItem(id));
  };

  const handleClearAll = () => {
    clearHistory();
    setItems([]);
    setConfirmClear(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Summarization History
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Locally saved summaries from this browser session and prior runs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {items.length > 0 &&
            (confirmClear ? (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="rounded-xl bg-rose-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-rose-700 cursor-pointer"
                >
                  Confirm Clear All
                </button>
                <button
                  type="button"
                  onClick={() => setConfirmClear(false)}
                  className="rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmClear(true)}
                className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Clear History
              </button>
            ))}

          <Link
            to="/summarize"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            New Summary
          </Link>
        </div>
      </div>

      {items.length > 0 && (
        <div>
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search saved summaries by title or content..."
            aria-label="Search summarization history"
            className="w-full max-w-md rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
          />
        </div>
      )}

      {items.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center space-y-4 shadow-xs">
          <h2 className="text-lg font-semibold text-slate-900">No saved summaries yet</h2>
          <p className="text-sm text-slate-600 max-w-md mx-auto">
            Run your first text or document summarization and it will be saved here automatically for quick inspection.
          </p>
          <Link
            to="/summarize"
            className="inline-flex rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            Create First Summary
          </Link>
        </div>
      ) : filteredItems.length === 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-600">
          No history entries match &ldquo;{query}&rdquo;.
        </div>
      ) : (
        <div className="space-y-3.5">
          {filteredItems.map((item) => (
            <article
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <div className="space-y-2 min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 font-medium text-slate-700 uppercase">
                    {item.sourceType || 'text'}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 font-medium text-indigo-700">
                    {LENGTH_LABELS[item.summaryLength] || item.summaryLength}
                  </span>
                  <span className="text-slate-400">·</span>
                  <time className="text-slate-500">{formatTimestamp(item.createdAt)}</time>
                </div>

                <h2 className="text-sm font-semibold text-slate-900 truncate">
                  {item.sourceName || 'Untitled Document'}
                </h2>

                <p className="text-sm text-slate-600 line-clamp-2">
                  {item.result?.extractive_summary}
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleOpenResult(item)}
                  className="rounded-xl bg-indigo-50 px-4 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors cursor-pointer"
                >
                  View Results
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  className="rounded-xl border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:text-rose-600 hover:border-rose-200 transition-colors cursor-pointer"
                >
                  Delete
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

export default History;
