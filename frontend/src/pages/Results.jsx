import { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import EvidenceViewer from '../components/EvidenceViewer';
import QualityDashboard from '../components/QualityDashboard';
import SummaryCard from '../components/SummaryCard';
import VerificationCard from '../components/VerificationCard';
import { extractClaims } from '../services/api';
import { getHistory } from '../services/history';

function Results() {
  const location = useLocation();
  const routeState = location.state;

  const entry = useMemo(() => {
    if (routeState?.result) {
      return routeState;
    }
    const latest = getHistory()[0];
    if (!latest) return null;
    return {
      result: latest.result,
      summaryLength: latest.summaryLength,
      sourceType: latest.sourceType,
      sourceName: latest.sourceName,
      claims: latest.claims || [],
      createdAt: latest.createdAt,
      fromHistoryFallback: true,
    };
  }, [routeState]);

  const summaryText = entry?.result?.extractive_summary || '';
  const hasPreloadedClaims = Boolean(
    entry?.claimsChecked || (entry?.claims && entry.claims.length > 0)
  );

  const [fetchedClaims, setFetchedClaims] = useState({
    targetKey: '',
    claims: [],
    error: '',
  });

  const needsFetch = Boolean(
    summaryText && !hasPreloadedClaims && fetchedClaims.targetKey !== summaryText
  );

  useEffect(() => {
    if (!needsFetch) {
      return;
    }

    let cancelled = false;
    extractClaims(summaryText)
      .then((payload) => {
        if (!cancelled) {
          setFetchedClaims({
            targetKey: summaryText,
            claims: payload?.claims || [],
            error: '',
          });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setFetchedClaims({
            targetKey: summaryText,
            claims: [],
            error: err?.message || 'Claim extraction unavailable.',
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [needsFetch, summaryText]);

  const claims = hasPreloadedClaims
    ? entry?.claims || []
    : fetchedClaims.targetKey === summaryText
      ? fetchedClaims.claims
      : [];

  const claimsError = hasPreloadedClaims
    ? entry?.claimsError || ''
    : fetchedClaims.targetKey === summaryText
      ? fetchedClaims.error
      : '';

  const claimsLoading = needsFetch;

  if (!entry?.result) {
    return (
      <div className="max-w-xl mx-auto rounded-2xl border border-slate-200 bg-white p-10 text-center space-y-4 shadow-xs">
        <h1 className="text-2xl font-bold text-slate-900">No Summary Selected</h1>
        <p className="text-sm text-slate-600">
          Submit a text passage or document file to inspect its extractive summary, quality metrics, and grounded sentences.
        </p>
        <div className="pt-2 flex justify-center gap-3">
          <Link
            to="/summarize"
            className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            Summarize Now
          </Link>
          <Link
            to="/history"
            className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            Browse History
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            Summarization Results
          </h1>
          <p className="text-sm text-slate-600 mt-0.5">
            {entry.fromHistoryFallback
              ? 'Showing your most recent saved summarization.'
              : 'Inspect the generated summary, sentence rankings, and extracted claims.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/history"
            className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
          >
            History
          </Link>
          <Link
            to="/summarize"
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 transition-colors"
          >
            Summarize Another
          </Link>
        </div>
      </div>

      <SummaryCard
        result={entry.result}
        summaryLength={entry.summaryLength}
        sourceName={entry.sourceName}
      />

      <QualityDashboard
        result={entry.result}
        summaryLength={entry.summaryLength}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <EvidenceViewer
          result={entry.result}
          claims={claims}
          claimsLoading={claimsLoading}
          claimsError={claimsError}
        />
        <VerificationCard
          claims={claims}
          claimsLoading={claimsLoading}
          claimsError={claimsError}
        />
      </div>
    </div>
  );
}

export default Results;
