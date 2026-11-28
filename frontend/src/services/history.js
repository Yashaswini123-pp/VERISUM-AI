const HISTORY_STORAGE_KEY = 'verisum_ai_history_v1';
const MAX_HISTORY_ITEMS = 25;

/**
 * Load all saved summarization entries from localStorage.
 * @returns {Array<any>}
 */
export function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

/**
 * Persist a new summarization entry at the top of localStorage history.
 * @param {{
 *   sourceType: 'text' | 'file',
 *   sourceName: string,
 *   summaryLength: string,
 *   result: any,
 *   claims?: Array<any>
 * }} entry
 * @returns {any}
 */
export function saveToHistory(entry) {
  const existing = getHistory();
  const item = {
    id:
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    createdAt: new Date().toISOString(),
    sourceType: entry.sourceType,
    sourceName: entry.sourceName,
    summaryLength: entry.summaryLength,
    result: entry.result,
    claims: entry.claims || [],
  };

  const next = [item, ...existing].slice(0, MAX_HISTORY_ITEMS);
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Ignore storage quota errors so summarization flow is never blocked.
  }
  return item;
}

/**
 * Delete a single entry from history by id.
 * @param {string} id
 * @returns {Array<any>}
 */
export function deleteHistoryItem(id) {
  const next = getHistory().filter((item) => item.id !== id);
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Ignore storage errors.
  }
  return next;
}

/**
 * Clear all saved summarization history.
 */
export function clearHistory() {
  try {
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  } catch {
    // Ignore storage errors.
  }
}
