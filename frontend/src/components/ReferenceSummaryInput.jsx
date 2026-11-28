import { useState } from 'react';

function ReferenceSummaryInput({ value, onChange, disabled = false }) {
  const [expanded, setExpanded] = useState(Boolean(value));

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5">
      <div className="flex items-center justify-between gap-2">
        <div>
          <span className="text-xs font-semibold text-slate-700">
            Reference Summary (Optional — for ROUGE Evaluation)
          </span>
          <p className="text-[11px] text-slate-500">
            ROUGE-1, ROUGE-2, and ROUGE-L are calculated only when a reference summary is supplied.
          </p>
        </div>
        <button
          type="button"
          disabled={disabled}
          onClick={() => {
            if (expanded && value) {
              onChange('');
            }
            setExpanded((prev) => !prev);
          }}
          className="shrink-0 text-xs font-medium text-indigo-600 hover:text-indigo-700 cursor-pointer disabled:opacity-50"
        >
          {expanded ? 'Hide' : 'Add Reference'}
        </button>
      </div>

      {expanded && (
        <textarea
          rows={3}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste a gold/reference summary to evaluate ROUGE-1, ROUGE-2, and ROUGE-L..."
          aria-label="Optional reference summary"
          className="mt-3 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:bg-slate-100"
        />
      )}
    </div>
  );
}

export default ReferenceSummaryInput;
