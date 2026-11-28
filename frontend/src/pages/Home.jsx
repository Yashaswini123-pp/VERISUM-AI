import { Link } from 'react-router-dom';

const PIPELINE_STEPS = [
  {
    step: '01',
    title: 'Document & Text Ingestion',
    description:
      'Paste raw text directly or upload PDF, DOCX, and TXT files. Text is cleaned and tokenized into indexed sentences.',
  },
  {
    step: '02',
    title: 'Extractive TextRank Summarization',
    description:
      'TF-IDF cosine similarity and PageRank score every sentence, selecting top-ranked statements in original order.',
  },
  {
    step: '03',
    title: 'Evidence Grounding & Claim Inspection',
    description:
      'Trace every summary sentence back to its source index, inspect salience scores, and surface factual claims.',
  },
];

const SUPPORTED_MODES = [
  { label: 'Short (~20%)', detail: 'Rapid executive takeaways' },
  { label: 'Medium (~35%)', detail: 'Balanced narrative summary' },
  { label: 'Detailed (~50%)', detail: 'High-retention document digest' },
];

function Home() {
  return (
    <div className="space-y-12 py-4">
      <section className="rounded-3xl border border-slate-200 bg-white px-6 py-12 sm:px-12 sm:py-16 shadow-xs">
        <div className="max-w-3xl space-y-6">
          <span className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 border border-indigo-200">
            Evidence-Grounded AI Summarization
          </span>

          <h1 className="text-3xl sm:text-5xl font-bold tracking-tight text-slate-900 leading-tight">
            Summarize complex documents with full source traceability.
          </h1>

          <p className="text-base sm:text-lg text-slate-600 leading-relaxed">
            VeriSum AI transforms raw text and uploaded PDF, DOCX, or TXT files into concise
            extractive summaries powered by TF-IDF and TextRank—preserving sentence IDs,
            ranking scores, and claim visibility at every step.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link
              to="/summarize"
              className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 transition-colors"
            >
              Start Summarizing
            </Link>
            <Link
              to="/history"
              className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              View History
            </Link>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-slate-900">How VeriSum AI Works</h2>
          <span className="text-xs font-medium text-slate-500">3-stage pipeline</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {PIPELINE_STEPS.map((item) => (
            <div
              key={item.step}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-3"
            >
              <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-50 text-xs font-bold text-indigo-700 border border-indigo-100">
                {item.step}
              </span>
              <h3 className="text-base font-semibold text-slate-900">{item.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <h2 className="text-lg font-semibold text-slate-900">
              Configurable Compression Levels
            </h2>
            <p className="text-sm text-slate-600">
              Choose how tightly the extractive summarizer condenses your document.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 flex-1 max-w-2xl">
            {SUPPORTED_MODES.map((mode) => (
              <div
                key={mode.label}
                className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <p className="text-sm font-semibold text-slate-900">{mode.label}</p>
                <p className="text-xs text-slate-500 mt-0.5">{mode.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
