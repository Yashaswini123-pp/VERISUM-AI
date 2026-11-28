const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Parse FastAPI error payloads into a human-readable message.
 * @param {Response} response
 * @returns {Promise<string>}
 */
async function parseErrorMessage(response) {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === 'string') {
      return payload.detail;
    }
    if (Array.isArray(payload?.detail) && payload.detail.length > 0) {
      return payload.detail.map((item) => item.msg || JSON.stringify(item)).join('; ');
    }
    if (payload?.message) {
      return payload.message;
    }
  } catch {
    // Response body is not JSON; fall through to status text.
  }
  return `Request failed (${response.status} ${response.statusText || 'Error'})`;
}

/**
 * Execute a fetch call with uniform error handling.
 * @param {string} path
 * @param {RequestInit} options
 * @returns {Promise<any>}
 */
async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      `Unable to reach the VeriSum AI backend at ${BASE_URL}. Make sure the FastAPI server is running.`
    );
  }

  if (!response.ok) {
    const message = await parseErrorMessage(response);
    throw new Error(message);
  }

  return response.json();
}

/**
 * Check backend service health.
 * @returns {Promise<{ status: string, service: string }>}
 */
export async function checkHealth() {
  return request('/');
}

/**
 * Summarize raw text using the integrated Member 2A + 2B summarization pipeline.
 * @param {string} text
 * @param {'short' | 'medium' | 'detailed'} summaryLength
 * @param {string} referenceSummary
 * @returns {Promise<any>}
 */
export async function summarizeText(
  text,
  summaryLength = 'medium',
  referenceSummary = ''
) {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('summary_length', summaryLength);
  if (referenceSummary && referenceSummary.trim()) {
    formData.append('reference_summary', referenceSummary.trim());
  }

  return request('/summarize/text', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Summarize an uploaded PDF, DOCX, or TXT file.
 * @param {File} file
 * @param {'short' | 'medium' | 'detailed'} summaryLength
 * @param {string} referenceSummary
 * @returns {Promise<any>}
 */
export async function summarizeFile(
  file,
  summaryLength = 'medium',
  referenceSummary = ''
) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('summary_length', summaryLength);
  if (referenceSummary && referenceSummary.trim()) {
    formData.append('reference_summary', referenceSummary.trim());
  }

  return request('/summarize/file', {
    method: 'POST',
    body: formData,
  });
}

/**
 * Extract factual claims from summary text using Member 3's claim extraction module.
 * @param {string} text
 * @param {number} threshold
 * @returns {Promise<{
 *   claims: Array<any>,
 *   total_sentences: number,
 *   errors: string[]
 * }>}
 */
export async function extractClaims(text, threshold = 0.55) {
  const formData = new FormData();
  formData.append('text', text);
  formData.append('threshold', String(threshold));

  return request('/claims/extract', {
    method: 'POST',
    body: formData,
  });
}
