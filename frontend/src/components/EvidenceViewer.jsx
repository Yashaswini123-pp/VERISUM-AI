import { useMemo } from 'react';

function EvidenceViewer({
  result,
  evidenceItems = [],
  claims = [],
  claimsLoading = false,
  claimsError = '',
}) {
  const groundedSentences = useMemo(() => {
    if (!result?.sentences || !result?.selected_sentence_ids) return [];
    const selectedSet = new Set(result.selected_sentence_ids);
    const scoreMap = new Map(
      (result.sentence_scores || []).map((item) => [item.id, item.score])
    );
    return result.sentences
      .filter((s) => selectedSet.has(s.id))
      .map((s) => ({
        ...s,
        score: scoreMap.get(s.id) ?? null,
      }));
  }, [result]);

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-xs p-6 space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">Evidence Viewer</h2>
        <p className="text-xs text-slate-500">
          Direct sentence grounding in the source document and retrieved verification evidence
        </p>
      </div>

      {/* Source Document Grounding */}
      <div className="space-y-2.5">
        <h3 className="text-sm font-semibold text-slate-800">
          Source Document Grounding ({groundedSentences.length} sentences)
        </h3>
        {groundedSentences.length === 0 ? (
          <p className="text-sm text-slate-500">
            No source sentence mappings available.
          </p>
        ) : (
          <div className="space-y-2">
            {groundedSentences.map((item) => (
              <div
                key={item.id}
                className="rounded-xl border border-slate-200 bg-slate-50/70 p-3.5 text-sm"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-xs font-semibold text-indigo-700">
                    Source Sentence #{item.id}
                  </span>
                  {typeof item.score === 'number' && (
                    <span className="text-xs font-mono text-slate-500">
                      TextRank: {item.score.toFixed(4)}
                    </span>
                  )}
                </div>
                <p className="text-slate-700 leading-relaxed">{item.text}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* External / Retrieved Evidence (Member 3 Evidence schema compatible) */}
      <div className="space-y-2.5 pt-4 border-t border-slate-100">
        <h3 className="text-sm font-semibold text-slate-800">
          Retrieved Verification Evidence
        </h3>

        {evidenceItems.length > 0 ? (
          <div className="space-y-2.5">
            {evidenceItems.map((ev, index) => {
              const relevancePct = Math.round((ev.relevance || 0) * 100);
              return (
                <div
                  key={`${ev.source}-${index}`}
                  className="rounded-xl border border-slate-200 bg-white p-4 space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2 text-xs">
                    <span className="font-semibold text-slate-700">
                      Source: {ev.source || 'Unknown'}
                    </span>
                    <span className="rounded-full bg-indigo-50 px-2 py-0.5 font-medium text-indigo-700">
                      {relevancePct}% relevance
                    </span>
                  </div>
                  <p className="text-sm text-slate-700 leading-relaxed">{ev.text}</p>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-4 text-xs text-slate-600 space-y-1">
            {claimsLoading ? (
              <p>Extracting factual claims from summary...</p>
            ) : claimsError ? (
              <p className="text-amber-700">
                Claim extraction unavailable: {claimsError}
              </p>
            ) : (
              <p>
                {claims.length > 0
                  ? `${claims.length} factual claim${claims.length === 1 ? '' : 's'} extracted from the summary. External evidence retrieval will appear here once Member 3's evidence retriever is connected.`
                  : 'External evidence retrieval is not yet connected (pending Member 3 retrieval service). Source sentence grounding above shows exact source traceability.'}
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

export default EvidenceViewer;
