const { test } = require("node:test");
const assert = require("node:assert/strict");

const {
  severityOf,
  pageUrl,
  relativeTime,
  exactTime,
  formatByteChange,
  formatChangeColumn,
  computePagination,
} = require("../src/wikiguard_py/static/dashboard.js");

// ---- severityOf -------------------------------------------------------

test("severityOf: below 500 is low", () => {
  assert.equal(severityOf({ byte_change: 100 }), "low");
});

test("severityOf: exactly 499 is low", () => {
  assert.equal(severityOf({ byte_change: 499 }), "low");
});

test("severityOf: exactly 500 is medium", () => {
  assert.equal(severityOf({ byte_change: 500 }), "medium");
});

test("severityOf: exactly 4999 is medium", () => {
  assert.equal(severityOf({ byte_change: 4999 }), "medium");
});

test("severityOf: exactly 5000 is high", () => {
  assert.equal(severityOf({ byte_change: 5000 }), "high");
});

test("severityOf: uses absolute value for negative byte_change", () => {
  assert.equal(severityOf({ byte_change: -9000 }), "high");
});

// ---- pageUrl ------------------------------------------------------------

test("pageUrl: builds a /wiki/ URL from server_name and page_title", () => {
  const url = pageUrl({ server_name: "en.wikipedia.org", page_title: "Some Page" });
  assert.equal(url, "https://en.wikipedia.org/wiki/Some%20Page");
});

test("pageUrl: encodes special characters in the title", () => {
  const url = pageUrl({ server_name: "he.wikipedia.org", page_title: "עמוד & דף" });
  assert.ok(url.startsWith("https://he.wikipedia.org/wiki/"));
  assert.ok(!url.includes("&"));
});

// ---- relativeTime ---------------------------------------------------------

test("relativeTime: just now for under a minute", () => {
  const now = new Date("2026-01-01T12:00:30Z").getTime();
  assert.equal(relativeTime("2026-01-01T12:00:00", now), "לפני רגע");
});

test("relativeTime: minutes ago under an hour", () => {
  const now = new Date("2026-01-01T12:10:00Z").getTime();
  assert.equal(relativeTime("2026-01-01T12:00:00", now), "לפני 10 דקות");
});

test("relativeTime: hours ago under a day", () => {
  const now = new Date("2026-01-01T15:00:00Z").getTime();
  assert.equal(relativeTime("2026-01-01T12:00:00", now), "לפני 3 שעות");
});

test("relativeTime: days ago at and beyond 24 hours", () => {
  const now = new Date("2026-01-03T12:00:00Z").getTime();
  assert.equal(relativeTime("2026-01-01T12:00:00", now), "לפני 2 ימים");
});

test("relativeTime: defaults to the real clock when now is omitted", () => {
  const result = relativeTime(new Date().toISOString().slice(0, -1));
  assert.equal(result, "לפני רגע");
});

// ---- exactTime --------------------------------------------------------

test("exactTime: formats a naive-UTC timestamp as a locale string", () => {
  const result = exactTime("2026-01-01T12:00:00");
  assert.equal(typeof result, "string");
  assert.ok(result.length > 0);
});

// ---- formatByteChange -----------------------------------------------------

test("formatByteChange: positive values get an explicit plus sign", () => {
  assert.equal(formatByteChange(500), "+500");
});

test("formatByteChange: negative values keep their own minus sign", () => {
  assert.equal(formatByteChange(-500), "-500");
});

test("formatByteChange: zero gets no sign", () => {
  assert.equal(formatByteChange(0), "0");
});

// ---- formatChangeColumn ---------------------------------------------------

test("formatChangeColumn: WindowCountEvaluator alert shows edit count", () => {
  const result = formatChangeColumn({
    rule_type: "WindowCountEvaluator",
    edit_count: 7,
    byte_change: 100,
  });
  assert.equal(result, "7 עריכות");
});

test("formatChangeColumn: ThresholdEvaluator alert shows byte change", () => {
  const result = formatChangeColumn({
    rule_type: "ThresholdEvaluator",
    edit_count: null,
    byte_change: 9000,
  });
  assert.equal(result, "+9000");
});

test("formatChangeColumn: WindowCountEvaluator with null edit_count falls back to byte change", () => {
  const result = formatChangeColumn({
    rule_type: "WindowCountEvaluator",
    edit_count: null,
    byte_change: 100,
  });
  assert.equal(result, "+100");
});

// ---- computePagination -----------------------------------------------------

test("computePagination: first page has no previous", () => {
  const { currentPage, hasPrev, hasNext } = computePagination(100, 10, 0);
  assert.equal(currentPage, 1);
  assert.equal(hasPrev, false);
  assert.equal(hasNext, true);
});

test("computePagination: middle page has both prev and next", () => {
  const { currentPage, hasPrev, hasNext } = computePagination(100, 10, 20);
  assert.equal(currentPage, 3);
  assert.equal(hasPrev, true);
  assert.equal(hasNext, true);
});

test("computePagination: last page has no next", () => {
  const { currentPage, totalPages, hasNext } = computePagination(100, 10, 90);
  assert.equal(currentPage, 10);
  assert.equal(totalPages, 10);
  assert.equal(hasNext, false);
});

test("computePagination: empty table still reports a single page", () => {
  const { totalPages, hasNext } = computePagination(0, 10, 0);
  assert.equal(totalPages, 1);
  assert.equal(hasNext, false);
});

test("computePagination: total not evenly divisible by limit rounds the page count up", () => {
  const { totalPages } = computePagination(25, 10, 0);
  assert.equal(totalPages, 3);
});
