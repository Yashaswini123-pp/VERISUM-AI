import { useMemo, useState } from 'react';
import { LENGTH_LABELS } from '../constants/summarization';

function SummaryCard({ result, summaryLength = 'medium', sourceName = '' }) {
  const [extractiveView, setExtractiveView] = useState('summary');
  const [copiedKey, setCopiedKey] = useState('');
  const [showChunks, setShowChunks] = useState(false);

  const selectedSet = useMemo(
    () => new Set(result?.selected_sentence_ids || []),
    [result?.selected_sentence_ids]
  );

  const scoreById = useMemo(() => {
    const map = new Map();
    for (const item of result?.sentence_scores || []) {
      map.set(item.id, item.score);
    }
    return map;
  }, [result?.sentence_scores]);

  if (!result) {
    return null;
  }

  const handleCopy = async (text, key) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(''), 1800);
    } catch {
      // Clipboard may be unavailable in restricted contexts.
    }
  };

  const chunking = result.chunking;
  const abstractiveMeta = result.abstractive_metadata;

  return (
    <div className="space-y-6">
      {/* Dual Summaries: Extractive & Abstractive displayed separately */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extractive Summary Panel */}
        <section className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 px-5 py-4 flex flex-wrap items-center justify-between gap-3 bg-slate-50/60">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-semibold text-slate-900">
                  Extractive Summary
                </h2>
                <span className="inline-flex items-center rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 border border-indigo-200">
                  {LENGTH_LABELS[summaryLength] || summaryLength}
                </span>
                {chunking?.chunking_used && (
                  <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700 border border-emerald-200">
                    Hierarchical ({chunking.chunk_count} chunks)
                  </span>
                )}
              </div>
              {sourceName && (
                <p className="text-xs text-slate-500 mt-0.5 truncate max-w-xs">
                  Source: {sourceName}
                </p>
              )}
            </div>

            <div className="flex items-center gap-2">
              <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setExtractiveView('summary')}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                    extractiveView === 'summary'
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Summary
                </button>
                <button
                  type="button"
                  onClick={() => setExtractiveView('highlighted')}
                  className={`px-2.5 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                    extractiveView === 'highlighted'
                      ? 'bg-indigo-600 text-white'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  Source
                </button>
              </div>

              <button
                type="button"
                onClick={() => handleCopy(result.extractive_summary, 'extractive')}
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
              >
                {copiedKey === 'extractive' ? 'Copied!' : 'Copy'}
              </button>
            </div>
          </div>

          <div className="p-5 flex-1">
            {extractiveView === 'summary' ? (
              <div className="space-y-4">
                <p className="text-sm sm:text-base leading-relaxed text-slate-800 whitespace-pre-line">
                  {result.extractive_summary || 'No extractive summary generated.'}
                </p>

                {result.selected_sentence_ids?.length > 0 && (
                  <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-1.5 text-xs text-slate-500">
                    <span className="font-medium text-slate-600">Selected sentences:</span>
                    {result.selected_sentence_ids.map((id) => (
                      <span
                        key={id}
                        className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-0.5 font-medium text-emerald-700 border border-emerald-200"
                      >
                        #{id}
                        {scoreById.has(id) && (
                          <span className="text-emerald-600">
                            ({scoreById.get(id).toFixed(3)})
                          </span>
                        )}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {(result.sentences || []).map((sentence) => {
                  const isSelected = selectedSet.has(sentence.id);
                  const score = scoreById.get(sentence.id);
                  return (
                    <div
                      key={sentence.id}
                      className={`rounded-xl border px-3.5 py-2.5 text-xs sm:text-sm transition-colors ${
                        isSelected
                          ? 'border-emerald-300 bg-emerald-50/70 text-slate-900'
                          : 'border-slate-200 bg-slate-50/40 text-slate-600'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2.5">
                        <div className="flex items-start gap-2">
                          <span
                            className={`mt-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-[11px] font-semibold ${
                              isSelected
                                ? 'bg-emerald-600 text-white'
                                : 'bg-slate-200 text-slate-700'
                            }`}
                          >
                            {sentence.id}
                          </span>
                          <p className="leading-relaxed">{sentence.text}</p>
                        </div>
                        {typeof score === 'number' && (
                          <span className="shrink-0 text-[11px] font-mono text-slate-500">
                            {score.toFixed(3)}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </section>

        {/* Abstractive Summary Panel */}
        <section className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden flex flex-col">
          <div className="border-b border-slate-200 px-5 py-4 flex flex-wrap items-center justify-between gap-3 bg-indigo-50/40">
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-semibold text-slate-900">
                  Abstractive Summary
                </h2>
                <span className="inline-flex items-center rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-medium text-purple-700 border border-purple-200">
                  {abstractiveMeta?.method === 'transformers_seq2seq'
                    ? abstractiveMeta.model
                    : 'Local Abstractive Fusion'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Compressed, non-redundant proposition synthesis
              </p>
            </div>

            <button
              type="button"
              onClick={() => handleCopy(result.abstractive_summary, 'abstractive')}
              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors cursor-pointer"
            >
              {copiedKey === 'abstractive' ? 'Copied!' : 'Copy'}
            </button>
          </div>

          <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
            <p className="text-sm sm:text-base leading-relaxed text-slate-800 whitespace-pre-line">
              {result.abstractive_summary ||
                'Abstractive summary is not available for this saved entry.'}
            </p>

            {abstractiveMeta && (
              <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center gap-2 text-xs text-slate-500">
                <span className="rounded-md bg-slate-100 px-2 py-0.5 font-medium text-slate-700">
                  Engine: {abstractiveMeta.model}
                </span>
                {abstractiveMeta.hierarchical_used && (
                  <span className="rounded-md bg-indigo-50 px-2 py-0.5 font-medium text-indigo-700">
                    Synthesized across {abstractiveMeta.source_chunks_synthesized} chunks
                  </span>
                )}
              </div>
            )}
          </div>
        </section>
      </div>

      {/* Long-Document Chunk Breakdown */}
      {chunking?.chunking_used && chunking.chunks?.length > 0 && (
        <section className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
          <div className="px-5 py-3.5 flex items-center justify-between gap-3 bg-slate-50/70">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">
                Hierarchical Chunk Breakdown ({chunking.chunk_count} overlapping chunks)
              </h3>
              <p className="text-xs text-slate-500">
                Sentence-boundary chunking with {chunking.overlap_sentences}-sentence overlap for context continuity
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowChunks((prev) => !prev)}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 cursor-pointer"
            >
              {showChunks ? 'Hide Chunks' : 'Inspect Chunks'}
            </button>
          </div>

          {showChunks && (
            <div className="p-5 border-t border-slate-200 grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {chunking.chunks.map((chunk) => (
                <div
                  key={chunk.chunk_index}
                  className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-2"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    <span className="font-semibold text-slate-800">
                      Chunk #{chunk.chunk_index + 1}
                    </span>
                    <span className="text-slate-500">
                      Sentences {chunk.sentence_ids[0]}–{chunk.sentence_ids[chunk.sentence_ids.length - 1]} ({chunk.word_count} words)
                    </span>
                  </div>
                  {chunk.overlap_sentence_ids?.length > 0 && (
                    <p className="text-[11px] text-indigo-700 font-medium">
                      Overlap carried from previous chunk: #{chunk.overlap_sentence_ids.join(', #')}
                    </p>
                  )}
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {chunk.chunk_summary}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default SummaryCard;
