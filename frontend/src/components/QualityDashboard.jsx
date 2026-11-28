import { useMemo } from 'react';
import { LENGTH_LABELS } from '../constants/summarization';

function countWords(text) {
  if (!text || !text.trim()) return 0;
  return text.trim().split(/\s+/).length;
}

function formatPct(value) {
  if (typeof value !== 'number') return '—';
  return `${Math.round(value * 100)}%`;
}

function QualityDashboard({ result, summaryLength = 'medium' }) {
  const metrics = useMemo(() => {
    if (!result) return null;

    const sentences = result.sentences || [];
    const selectedIds = new Set(result.selected_sentence_ids || []);
    const scores = result.sentence_scores || [];

    const qm = result.quality_metrics || null;
    const originalWords = qm?.original_word_count ?? countWords(result.original_text);
    const extractiveWords =
      qm?.extractive?.word_count ?? countWords(result.extractive_summary);
    const abstractiveWords =
      qm?.abstractive?.word_count ?? countWords(result.abstractive_summary);

    const extCompression =
      qm?.compression_ratio ??
      (originalWords > 0 ? Number((extractiveWords / originalWords).toFixed(4)) : 0);
    const absCompression =
      qm?.abstractive_compression_ratio ??
      (originalWords > 0 && abstractiveWords > 0
        ? Number((abstractiveWords / originalWords).toFixed(4))
        : null);

    const allScores = scores.map((s) => s.score);
    const maxScore = allScores.length > 0 ? Math.max(...allScores) : 0;

    const sentenceTextMap = new Map(sentences.map((s) => [s.id, s.text]));
    const rankedSentences = [...scores]
      .sort((a, b) => b.score - a.score)
      .slice(0, 6)
      .map((item) => ({
        ...item,
        text: sentenceTextMap.get(item.id) || '',
        selected: selectedIds.has(item.id),
      }));

    return {
      totalSentences: sentences.length,
      selectedSentences: selectedIds.size,
      originalWords,
      extractiveWords,
      abstractiveWords,
      extCompression,
      absCompression,
      qm,
      maxScore,
      rankedSentences,
    };
  }, [result]);

  if (!metrics) {
    return null;
  }

  const extCoverage = metrics.qm?.sentence_coverage;
  const absCoverage = metrics.qm?.abstractive_coverage;
  const extRedundancy = metrics.qm?.redundancy?.extractive;
  const absRedundancy = metrics.qm?.redundancy?.abstractive;
  const rouge = metrics.qm?.rouge;

  const cards = [
    {
      label: 'Extractive Compression',
      value: metrics.extCompression.toFixed(2),
      sub: `${metrics.extractiveWords} / ${metrics.originalWords} words`,
    },
    {
      label: 'Abstractive Compression',
      value: metrics.absCompression !== null ? metrics.absCompression.toFixed(2) : '—',
      sub:
        metrics.abstractiveWords > 0
          ? `${metrics.abstractiveWords} / ${metrics.originalWords} words`
          : 'Not available',
    },
    {
      label: 'Sentence Coverage',
      value: extCoverage
        ? formatPct(extCoverage.semantic_coverage)
        : `${metrics.selectedSentences} / ${metrics.totalSentences}`,
      sub: extCoverage
        ? `${metrics.selectedSentences}/${metrics.totalSentences} sents · Concept ${formatPct(extCoverage.concept_coverage)}`
        : LENGTH_LABELS[summaryLength] || summaryLength,
    },
    {
      label: 'Redundancy Score',
      value: extRedundancy ? extRedundancy.redundancy_score.toFixed(3) : '—',
      sub: absRedundancy
        ? `Abstractive: ${absRedundancy.redundancy_score.toFixed(3)} (lower is better)`
        : 'Inter-sentence & bigram overlap',
    },
  ];

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-xs p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Quality Metrics Dashboard</h2>
          <p className="text-xs text-slate-500">
            Compression ratio, semantic/sentence coverage, redundancy, and optional ROUGE evaluation
          </p>
        </div>
        <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
          {LENGTH_LABELS[summaryLength] || summaryLength}
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        {cards.map((card) => (
          <div
            key={card.label}
            className="rounded-xl border border-slate-200 bg-slate-50/70 p-4"
          >
            <p className="text-xs font-medium text-slate-500">{card.label}</p>
            <p className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
              {card.value}
            </p>
            <p className="mt-1 text-xs text-slate-500">{card.sub}</p>
          </div>
        ))}
      </div>

      {/* Detailed Coverage & Redundancy Comparison */}
      {metrics.qm && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-200 bg-slate-50/40 p-4 space-y-1.5 text-xs">
            <h3 className="font-semibold text-slate-800">Extractive Profile</h3>
            <p className="text-slate-600">
              Selected sentences: {formatPct(extCoverage?.selected_sentence_ratio)} · Semantic coverage:{' '}
              {formatPct(extCoverage?.semantic_coverage)} · Concept coverage:{' '}
              {formatPct(extCoverage?.concept_coverage)}
            </p>
            <p className="text-slate-600">
              Pairwise similarity: {extRedundancy?.pairwise_similarity?.toFixed(3)} · Bigram repetition:{' '}
              {extRedundancy?.ngram_repetition_rate?.toFixed(3)}
            </p>
          </div>

          <div className="rounded-xl border border-slate-200 bg-indigo-50/30 p-4 space-y-1.5 text-xs">
            <h3 className="font-semibold text-slate-800">Abstractive Profile</h3>
            <p className="text-slate-600">
              Semantic coverage: {formatPct(absCoverage?.semantic_coverage)} · Concept coverage:{' '}
              {formatPct(absCoverage?.concept_coverage)}
            </p>
            <p className="text-slate-600">
              Pairwise similarity: {absRedundancy?.pairwise_similarity?.toFixed(3)} · Bigram repetition:{' '}
              {absRedundancy?.ngram_repetition_rate?.toFixed(3)}
            </p>
          </div>
        </div>
      )}

      {/* ROUGE Evaluation (only displayed when a genuine reference summary was supplied) */}
      {rouge && (
        <div className="rounded-xl border border-indigo-200 bg-indigo-50/30 p-4 space-y-3">
          <div>
            <h3 className="text-sm font-semibold text-slate-900">
              ROUGE Evaluation (Against Supplied Reference Summary)
            </h3>
            <p className="text-xs text-slate-500">
              F1 / Precision / Recall scores computed directly against your reference summary.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {['extractive', 'abstractive'].map((kind) => {
              const scores = rouge[kind];
              if (!scores) return null;
              return (
                <div
                  key={kind}
                  className="rounded-lg border border-slate-200 bg-white p-3 space-y-2"
                >
                  <p className="font-semibold text-slate-800 capitalize">{kind} Summary</p>
                  <div className="grid grid-cols-3 gap-2">
                    {['rouge1', 'rouge2', 'rougeL'].map((metricKey) => (
                      <div key={metricKey} className="rounded bg-slate-50 p-2">
                        <p className="font-semibold text-slate-700 uppercase">
                          {metricKey}
                        </p>
                        <p className="text-sm font-bold text-indigo-700">
                          {scores[metricKey]?.f1?.toFixed(3)}
                        </p>
                        <p className="text-[11px] text-slate-500">
                          P {scores[metricKey]?.precision?.toFixed(2)} · R{' '}
                          {scores[metricKey]?.recall?.toFixed(2)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Top TextRank Sentence Scores */}
      {metrics.rankedSentences.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-slate-800">
            Top TextRank Sentence Scores
          </h3>
          <div className="space-y-2.5">
            {metrics.rankedSentences.map((item) => {
              const barWidth =
                metrics.maxScore > 0
                  ? Math.max(8, Math.round((item.score / metrics.maxScore) * 100))
                  : 0;
              return (
                <div key={item.id} className="space-y-1">
                  <div className="flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2 min-w-0">
                      <span
                        className={`shrink-0 inline-flex items-center rounded px-1.5 py-0.5 font-semibold ${
                          item.selected
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        #{item.id}
                      </span>
                      <span className="truncate text-slate-700">{item.text}</span>
                    </div>
                    <span className="shrink-0 font-mono text-slate-600">
                      {item.score.toFixed(4)}
                    </span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        item.selected ? 'bg-emerald-500' : 'bg-indigo-400'
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}

export default QualityDashboard;
