const LABEL_STYLES = {
  Supported: {
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    border: 'border-emerald-200',
  },
  Contradicted: {
    badge: 'bg-rose-50 text-rose-700 border-rose-200',
    border: 'border-rose-200',
  },
  'Not Enough Information': {
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    border: 'border-amber-200',
  },
};

function VerificationCard({
  verificationResults = [],
  claims = [],
  claimsLoading = false,
  claimsError = '',
}) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-xs p-6 space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            Claim &amp; Fact Verification
          </h2>
          <p className="text-xs text-slate-500">
            Factual claims extracted from the generated summary
          </p>
        </div>
        {claims.length > 0 && verificationResults.length === 0 && (
          <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-700">
            {claims.length} {claims.length === 1 ? 'claim' : 'claims'} detected
          </span>
        )}
      </div>

      {verificationResults.length > 0 ? (
        <div className="space-y-3">
          {verificationResults.map((item, idx) => {
            const style =
              LABEL_STYLES[item.label] || LABEL_STYLES['Not Enough Information'];
            const confidencePct = Math.round((item.confidence || 0) * 100);
            return (
              <article
                key={`${item.claim_text}-${idx}`}
                className={`rounded-xl border ${style.border} bg-slate-50/40 p-4 space-y-2`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span
                    className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${style.badge}`}
                  >
                    {item.label}
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    Confidence: {confidencePct}%
                  </span>
                </div>
                <p className="text-sm font-medium text-slate-900">{item.claim_text}</p>
                {item.evidence_text && (
                  <p className="text-xs text-slate-600 bg-white rounded-lg border border-slate-200 p-2.5">
                    <span className="font-semibold text-slate-700">Evidence: </span>
                    {item.evidence_text}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      ) : claimsLoading ? (
        <div className="flex items-center gap-2 text-sm text-slate-500 py-3">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
          Running claim extraction...
        </div>
      ) : claimsError ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
          Could not extract claims: {claimsError}
        </div>
      ) : claims.length > 0 ? (
        <div className="space-y-3">
          {claims.map((claim, idx) => {
            const confidencePct = Math.round((claim.confidence || 0) * 100);
            return (
              <article
                key={claim.id || idx}
                className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                    Claim Extracted · Verification Pending
                  </span>
                  <span className="text-xs font-mono text-slate-500">
                    Claim confidence: {confidencePct}%
                  </span>
                </div>
                <p className="text-sm text-slate-900">{claim.text}</p>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/70 p-4 text-xs text-slate-600">
          No factual claims detected in this summary, or claim verification is not yet connected.
        </div>
      )}
    </section>
  );
}

export default VerificationCard;
