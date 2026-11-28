export const SUMMARY_LENGTH_OPTIONS = [
  {
    value: 'short',
    label: 'Short',
    ratio: '~20%',
    description: 'Key highlights only',
  },
  {
    value: 'medium',
    label: 'Medium',
    ratio: '~35%',
    description: 'Balanced overview',
  },
  {
    value: 'detailed',
    label: 'Detailed',
    ratio: '~50%',
    description: 'Comprehensive coverage',
  },
];

export const LENGTH_LABELS = {
  short: 'Short (~20%)',
  medium: 'Medium (~35%)',
  detailed: 'Detailed (~50%)',
};

export const SAMPLE_DOCUMENT_TEXT =
  'Artificial intelligence is transforming modern healthcare by assisting clinicians with rapid diagnostic workflows. ' +
  'Machine learning models analyze medical imaging such as X-rays and MRI scans to identify subtle anomalies early. ' +
  'Clinical decision support systems cross-reference patient histories against peer-reviewed medical literature in seconds. ' +
  'However, automated summaries must remain grounded in verifiable source evidence to prevent hallucinations in high-stakes settings. ' +
  'Researchers continue to develop fact-checking pipelines that extract individual claims and validate them against primary documents. ' +
  'Hospitals adopting transparent AI tools report faster chart reviews while maintaining strict human oversight.';
