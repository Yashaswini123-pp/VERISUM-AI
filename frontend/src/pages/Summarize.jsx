import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import TextInput from '../components/TextInput';
import { extractClaims, summarizeFile, summarizeText } from '../services/api';
import { saveToHistory } from '../services/history';

const INPUT_TABS = [
  { id: 'text', label: 'Paste Text' },
  { id: 'file', label: 'Upload Document' },
];

function Summarize() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('text');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const completeSummarization = async ({
    promise,
    sourceType,
    sourceName,
    summaryLength,
  }) => {
    setIsLoading(true);
    setError('');

    try {
      const result = await promise;

      let claims = [];
      let claimsError = '';
      const textForClaims = result?.extractive_summary || result?.abstractive_summary;
      if (textForClaims) {
        try {
          const claimPayload = await extractClaims(textForClaims);
          claims = claimPayload?.claims || [];
        } catch (err) {
          claimsError = err?.message || 'Claim extraction unavailable.';
        }
      }

      const saved = saveToHistory({
        sourceType,
        sourceName,
        summaryLength,
        result,
        claims,
      });

      navigate('/results', {
        state: {
          result,
          summaryLength,
          sourceType,
          sourceName,
          claims,
          claimsError,
          claimsChecked: true,
          historyId: saved.id,
          createdAt: saved.createdAt,
        },
      });
    } catch (err) {
      setError(err?.message || 'Something went wrong while summarizing.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSubmit = (text, summaryLength, referenceSummary) => {
    const snippet = text.length > 60 ? `${text.slice(0, 60)}...` : text;
    completeSummarization({
      promise: summarizeText(text, summaryLength, referenceSummary),
      sourceType: 'text',
      sourceName: snippet,
      summaryLength,
    });
  };

  const handleFileSubmit = (file, summaryLength, referenceSummary) => {
    completeSummarization({
      promise: summarizeFile(file, summaryLength, referenceSummary),
      sourceType: 'file',
      sourceName: file.name,
      summaryLength,
    });
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
          Summarize Document
        </h1>
        <p className="text-sm text-slate-600">
          Paste text or upload a PDF, DOCX, or TXT file to generate extractive and abstractive summaries with quality metrics.
        </p>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div
          className="flex border-b border-slate-200 bg-slate-50/70 px-4 pt-3 gap-2"
          role="tablist"
          aria-label="Input method"
        >
          {INPUT_TABS.map((tab) => {
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={isSelected}
                disabled={isLoading}
                onClick={() => {
                  setActiveTab(tab.id);
                  setError('');
                }}
                className={`px-4 py-2.5 text-sm font-medium rounded-t-xl border-b-2 transition-colors cursor-pointer disabled:opacity-60 ${
                  isSelected
                    ? 'border-indigo-600 text-indigo-700 bg-white'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {error && (
            <div
              role="alert"
              className="mb-5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700"
            >
              {error}
            </div>
          )}

          {activeTab === 'text' ? (
            <TextInput onSubmit={handleTextSubmit} isLoading={isLoading} />
          ) : (
            <FileUpload onSubmit={handleFileSubmit} isLoading={isLoading} />
          )}
        </div>
      </div>
    </div>
  );
}

export default Summarize;
