// Pure display-logic functions extracted out of dashboard.html's inline
// script so they can be unit-tested with Node (tests_js/dashboard.test.js)
// without a browser or DOM. Loaded as a plain classic script before the
// dashboard's own inline <script>, so these stay ordinary globals there —
// the module.exports guard below only matters when Node requires this file.

// Severity is a client-side read of byte_change — no backend concept of
// "severity" exists, this is purely a display judgment.
function severityOf(alert) {
  const magnitude = Math.abs(alert.byte_change);
  if (magnitude >= 5000) return "high";
  if (magnitude >= 500) return "medium";
  return "low";
}

// Wikimedia page URLs follow /wiki/<title> on the edit's own server_name —
// this works for every project (Wikipedia, Wikidata, Wiktionary, ...).
function pageUrl(alert) {
  return `https://${alert.server_name}/wiki/${encodeURIComponent(alert.page_title)}`;
}

// Postgres returns a UTC timestamp with no "Z"/offset suffix — without it,
// `new Date(...)` assumes *local* time, which silently shifts every value
// by the browser's UTC offset. Appending "Z" fixes that everywhere a
// fired_at string gets parsed. `now` defaults to the real clock but is
// injectable so tests get a fixed, reproducible "current time".
function relativeTime(isoString, now = Date.now()) {
  const date = new Date(isoString + "Z");
  const seconds = Math.floor((now - date.getTime()) / 1000);
  if (seconds < 60) return "לפני רגע";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `לפני ${minutes} דקות`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `לפני ${hours} שעות`;
  return `לפני ${Math.floor(hours / 24)} ימים`;
}

// Shown alongside the relative text, not just on hover — "when exactly"
// matters here (alerts can fire multiple times per second).
function exactTime(isoString) {
  return new Date(isoString + "Z").toLocaleString("he-IL", {
    dateStyle: "short",
    timeStyle: "medium",
  });
}

function formatByteChange(byteChange) {
  const sign = byteChange > 0 ? "+" : "";
  return `${sign}${byteChange}`;
}

// Window-Count alerts fire on edit *count*, not edit size — showing the
// triggering edit's byte_change there would be meaningless. Threshold
// alerts still show the byte change, which is the whole point of that rule.
function formatChangeColumn(alert) {
  if (alert.rule_type === "WindowCountEvaluator" && alert.edit_count != null) {
    return `${alert.edit_count} עריכות`;
  }
  return formatByteChange(alert.byte_change);
}

// Pure pagination arithmetic, pulled out of renderAlertsPagination (which
// still owns the DOM updates) so the page-count/button-state logic can be
// tested without a document.
function computePagination(total, limit, offset) {
  const totalPages = Math.max(1, Math.ceil(total / limit));
  const currentPage = Math.floor(offset / limit) + 1;
  return {
    totalPages,
    currentPage,
    hasPrev: offset > 0,
    hasNext: currentPage < totalPages,
  };
}

if (typeof module !== "undefined") {
  module.exports = {
    severityOf,
    pageUrl,
    relativeTime,
    exactTime,
    formatByteChange,
    formatChangeColumn,
    computePagination,
  };
}
