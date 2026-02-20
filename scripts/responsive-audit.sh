#!/usr/bin/env bash
# Minimal responsive audit: grep-based checks for mobile-first patterns.
# Exit 0 if all checks pass, 1 if any fail.

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB="$ROOT/apps/web/src"
FAILED=0

echo "=== Responsive Audit ==="

# 1. overflow-x-hidden on body or html
if grep -q "overflow-x" "$ROOT/apps/web/src/index.css" 2>/dev/null || grep -q "overflow-x" "$ROOT/apps/web/index.html" 2>/dev/null; then
  echo "  OK: overflow-x control found"
else
  echo "  WARN: No overflow-x control (expected in index.css or html)"
fi

# 2. Touch targets (min-h-touch, min-w-touch, or min-h-[44px])
TOUCH_COUNT=$(grep -r "min-h-touch\|min-w-touch\|min-h-\[44px\]" "$WEB" 2>/dev/null | wc -l)
if [ "$TOUCH_COUNT" -lt 5 ]; then
  echo "  FAIL: Expected at least 5 touch target usages (min-h-touch/min-w-touch), found $TOUCH_COUNT"
  FAILED=1
else
  echo "  OK: Found $TOUCH_COUNT touch target usages"
fi

# 3. Responsive breakpoints (md:, sm:, etc.)
BP_COUNT=$(grep -rE "md:|sm:|lg:" "$WEB" 2>/dev/null | wc -l)
if [ "$BP_COUNT" -lt 3 ]; then
  echo "  WARN: Few responsive breakpoints found ($BP_COUNT)"
else
  echo "  OK: Found $BP_COUNT responsive breakpoint usages"
fi

# 4. tailwind screens include xs/390
if [ -f "$ROOT/apps/web/tailwind.config.js" ]; then
  if grep -q "390px\|xs:" "$ROOT/apps/web/tailwind.config.js" 2>/dev/null; then
    echo "  OK: tailwind.config includes xs/390px breakpoint"
  else
    echo "  WARN: Consider adding xs:390px to tailwind screens"
  fi
fi

echo "=== Audit complete ==="
[ $FAILED -eq 0 ] || exit 1
