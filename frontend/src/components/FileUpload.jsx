import { useRef, useState } from 'react';
import LengthSelector from './LengthSelector';
import ReferenceSummaryInput from './ReferenceSummaryInput';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt'];

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function isAllowedFile(file) {
  if (!file?.name) return false;
  const lower = file.name.toLowerCase();
  return ALLOWED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

function FileUpload({ onSubmit, isLoading = false, initialLength = 'medium' }) {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [summaryLength, setSummaryLength] = useState(initialLength);
  const [referenceSummary, setReferenceSummary] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleFilePick = (file) => {
    if (!file) return;
    if (!isAllowedFile(file)) {
      setSelectedFile(null);
      setValidationError('Unsupported file format. Please select a PDF, DOCX, or TXT file.');
      return;
    }
    setValidationError('');
    setSelectedFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    if (isLoading) return;
    const droppedFile = event.dataTransfer.files?.[0];
    handleFilePick(droppedFile);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setValidationError('Please upload a PDF, DOCX, or TXT document first.');
      return;
    }
    setValidationError('');
    onSubmit(selectedFile, summaryLength, referenceSummary.trim());
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <span className="block text-sm font-medium text-slate-700 mb-2">
          Upload Document
        </span>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            if (!isLoading) setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => !isLoading && fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if ((e.key === 'Enter' || e.key === ' ') && !isLoading) {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
          className={`rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-indigo-500 bg-indigo-50/70'
              : 'border-slate-300 bg-slate-50/60 hover:border-indigo-400 hover:bg-slate-50'
          } ${isLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            disabled={isLoading}
            onChange={(e) => handleFilePick(e.target.files?.[0])}
            className="hidden"
          />

          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
            <svg
              className="h-6 w-6"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>

          <p className="text-sm font-medium text-slate-800">
            Drop your document here, or <span className="text-indigo-600">browse files</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Supports PDF, DOCX, and TXT documents
          </p>
        </div>

        {selectedFile && (
          <div className="mt-3 flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500">
                {formatFileSize(selectedFile.size)}
              </p>
            </div>
            <button
              type="button"
              disabled={isLoading}
              onClick={() => {
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="text-xs font-medium text-rose-600 hover:text-rose-700 cursor-pointer disabled:opacity-50"
            >
              Remove
            </button>
          </div>
        )}

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
              Processing Document...
            </>
          ) : (
            'Summarize Document'
          )}
        </button>
      </div>
    </form>
  );
}

export default FileUpload;
