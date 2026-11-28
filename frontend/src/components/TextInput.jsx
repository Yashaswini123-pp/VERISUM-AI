import { useState } from 'react';
import { SAMPLE_DOCUMENT_TEXT } from '../constants/summarization';
import LengthSelector from './LengthSelector';
import ReferenceSummaryInput from './ReferenceSummaryInput';

function TextInput({ onSubmit, isLoading = false, initialText = '', initialLength = 'medium' }) {
  const [text, setText] = useState(initialText);
  const [summaryLength, setSummaryLength] = useState(initialLength);
  const [referenceSummary, setReferenceSummary] = useState('');
  const [validationError, setValidationError] = useState('');

  const trimmed = text.trim();
  const wordCount = trimmed ? trimmed.split(/\s+/).length : 0;

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!trimmed) {
      setValidationError('Please enter or paste some text before generating a summary.');
      return;
    }
    setValidationError('');
    onSubmit(trimmed, summaryLength, referenceSummary.trim());
  };

  const handleLoadSample = () => {
    setText(SAMPLE_DOCUMENT_TEXT);
    setValidationError('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
          <label htmlFor="summarize-text-input" className="text-sm font-medium text-slate-700">
            Source Text
          </label>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleLoadSample}
              disabled={isLoading}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-700 cursor-pointer disabled:opacity-50"
            >
              Load sample text
            </button>
            {text && (
              <button
                type="button"
                onClick={() => {
                  setText('');
                  setValidationError('');
                }}
                disabled={isLoading}
                className="text-xs font-medium text-slate-500 hover:text-slate-700 cursor-pointer disabled:opacity-50"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <textarea
          id="summarize-text-input"
          rows={9}
          value={text}
          disabled={isLoading}
          onChange={(e) => {
            setText(e.target.value);
            if (validationError) setValidationError('');
          }}
          placeholder="Paste an article, research paper excerpt, report, or multi-sentence document here..."
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 disabled:bg-slate-50"
        />

        <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
          <span>
            {wordCount} {wordCount === 1 ? 'word' : 'words'} · {text.length} characters
          </span>
          <span>Long docs (&gt;220 words / &gt;12 sentences) auto-enable hierarchical chunking</span>
        </div>

        {validationError && (
          <p className="mt-2 text-sm text-rose-600" role="alert">
            {validationError}
          </p>
        )}
      </div>

      <LengthSelector
        value={summaryLength}
        onChange={setSummaryLength}
        disabled={isLoading}
      />

      <ReferenceSummaryInput
        value={referenceSummary}
        onChange={setReferenceSummary}
        disabled={isLoading}
      />

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Summarizing...
            </>
          ) : (
            'Generate Summary'
          )}
        </button>
      </div>
    </form>
  );
}

export default TextInput;
