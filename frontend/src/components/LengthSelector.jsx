import { SUMMARY_LENGTH_OPTIONS } from '../constants/summarization';

function LengthSelector({ value, onChange, disabled = false }) {
  return (
    <div>
      <span className="block text-sm font-medium text-slate-700 mb-2">
        Summary Length
      </span>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" role="radiogroup" aria-label="Summary length">
        {SUMMARY_LENGTH_OPTIONS.map((option) => {
          const isSelected = value === option.value;
          return (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={disabled}
              onClick={() => onChange(option.value)}
              className={`text-left rounded-xl border px-3.5 py-2.5 transition-all cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed ${
                isSelected
                  ? 'border-indigo-600 bg-indigo-50/70 ring-1 ring-indigo-600'
                  : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span
                  className={`text-sm font-semibold ${
                    isSelected ? 'text-indigo-900' : 'text-slate-900'
                  }`}
                >
                  {option.label}
                </span>
                <span
                  className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    isSelected
                      ? 'bg-indigo-100 text-indigo-700'
                      : 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {option.ratio}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">{option.description}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default LengthSelector;
