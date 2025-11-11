#!/usr/bin/env bash
# Smoke & health test for StatisticsAPI (and indirectly DeviceRegistrationAPI) on Arch Linux.
# - Waits for /readyz
# - Verifies /livez, /startupz, /readyz
# - Posts a login event and checks statistics increased
# - Negative validation test (400)
# - Optional "Unknown" device type flow
# Requirements: curl, jq

set -euo pipefail

# ------------- Pretty printing / colors -------------
if [[ -t 1 ]]; then
  RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BLUE=$'\033[34m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else
  RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; RESET=""
fi

log()   { printf "%s\n" "$*"; }
info()  { printf "%sℹ %s%s\n"   "$BLUE" "$*" "$RESET"; }
ok()    { printf "%s✔ %s%s\n"   "$GREEN" "$*" "$RESET"; }
warn()  { printf "%s⚠ %s%s\n"   "$YELLOW" "$*" "$RESET"; }
fail()  { printf "%s✖ %s%s\n"   "$RED" "$*" "$RESET"; }

# ------------- Defaults & CLI args -------------
STATS_URL="${STATS_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-120}"            # seconds to wait for /readyz
DEVICE_TYPE="${DEVICE_TYPE:-Android}"
RUN_UNKNOWN=1

usage() {
  cat <<EOF
Usage: $(basename "$0") [--stats-url URL] [--device-type TYPE] [--timeout SECONDS] [--skip-unknown]

Options:
  --stats-url URL     Base URL of StatisticsAPI (default: ${STATS_URL})
  --device-type TYPE  Device type used for positive flow (default: ${DEVICE_TYPE})
  --timeout SECONDS   Max seconds to wait for /readyz (default: ${TIMEOUT})
  --skip-unknown      Skip the "Unknown" device type scenario
  -h, --help          Show this help
Environment overrides:
  STATS_URL, DEVICE_TYPE, TIMEOUT
Exit codes: 0 on success, non-zero on any failure.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stats-url)     STATS_URL="$2"; shift 2;;
    --device-type)   DEVICE_TYPE="$2"; shift 2;;
    --timeout)       TIMEOUT="$2"; shift 2;;
    --skip-unknown)  RUN_UNKNOWN=0; shift;;
    -h|--help)       usage; exit 0;;
    *) fail "Unknown option: $1"; usage; exit 2;;
  esac
done

# ------------- Preconditions -------------
for cmd in curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || { fail "Missing dependency: $cmd"; exit 3; }
done

# ------------- HTTP helpers -------------
# Performs GET, prints body to stdout, sets global HTTP_STATUS
http_get() {
  local url="$1"; local timeout="${2:-5}"
  local resp
  resp="$(curl -sS -m "$timeout" -w $'\n%{http_code}' "$url")" || return 1
  HTTP_STATUS="${resp##*$'\n'}"
  printf "%s" "${resp%$'\n'*}"
  return 0
}

# Performs POST with JSON body, prints body to stdout, sets global HTTP_STATUS
http_post_json() {
  local url="$1"; local json="$2"; local timeout="${3:-5}"
  local resp
  resp="$(curl -sS -m "$timeout" -H 'Content-Type: application/json' -d "$json" -w $'\n%{http_code}' "$url")" || return 1
  HTTP_STATUS="${resp##*$'\n'}"
  printf "%s" "${resp%$'\n'*}"
  return 0
}

# ------------- Utility -------------
rand_id() {
  # 8-char random suffix
  tr -dc 'a-z0-9' </dev/urandom | head -c 8
}

get_count_for_type() {
  local dtype="$1"
  local body status
  body="$(http_get "${STATS_URL}/Log/auth/statistics?deviceType=${dtype}" 5 || true)"
  status="${HTTP_STATUS:-0}"
  if [[ "$status" != "200" ]]; then
    echo "-1"; return 1
  fi
  jq -r '.count // -1' <<<"$body"
}

wait_until_ready() {
  local deadline=$(( $(date +%s) + TIMEOUT ))
  while :; do
    local body
    body="$(http_get "${STATS_URL}/readyz" 3 || true)"
    if [[ "${HTTP_STATUS:-0}" == "200" ]]; then
      ok "Ready: ${STATS_URL}/readyz"
      return 0
    fi
    if (( $(date +%s) >= deadline )); then
      fail "Timeout waiting for readiness at ${STATS_URL}/readyz (last HTTP ${HTTP_STATUS:-?}, body: ${body:0:200})"
      return 1
    fi
    sleep 2
  done
}

# ------------- Tests -------------
TOTAL=0
FAILED=0
test_case() {
  TOTAL=$((TOTAL+1))
  local name="$1"; shift
  if "$@"; then
    ok "$name"
  else
    FAILED=$((FAILED+1))
    fail "$name"
  fi
}

test_livez() {
  local body
  body="$(http_get "${STATS_URL}/livez" 3 || true)"
  [[ "${HTTP_STATUS:-0}" == "200" ]] || { warn "livez status: ${HTTP_STATUS:-?}, body: $body"; return 1; }
  return 0
}

test_startupz() {
  local body
  body="$(http_get "${STATS_URL}/startupz" 3 || true)"
  [[ "${HTTP_STATUS:-0}" == "200" ]] || { warn "startupz status: ${HTTP_STATUS:-?}, body: $body"; return 1; }
  return 0
}

test_readyz() {
  local body
  body="$(http_get "${STATS_URL}/readyz" 3 || true)"
  [[ "${HTTP_STATUS:-0}" == "200" ]] || { warn "readyz status: ${HTTP_STATUS:-?}, body: $body"; return 1; }
  return 0
}

test_positive_flow() {
  local dtype="$1"
  local before after uid payload body status
  before="$(get_count_for_type "$dtype")" || true
  info "Baseline count for '${dtype}': ${before}"

  uid="smoke-$(rand_id)"
  payload=$(jq -nc --arg u "$uid" --arg d "$dtype" '{userKey:$u, deviceType:$d}')
  body="$(http_post_json "${STATS_URL}/Log/auth" "$payload" 5 || true)"
  status="${HTTP_STATUS:-0}"
  [[ "$status" == "200" ]] || { warn "POST /Log/auth failed: HTTP $status body=$body"; return 1; }
  [[ "$(jq -r '.statusCode // empty' <<<"$body")" == "200" ]] || { warn "POST /Log/auth invalid JSON: $body"; return 1; }

  # Poll statistics up to 10 times for eventual DB commit/visibility
  for _ in {1..10}; do
    after="$(get_count_for_type "$dtype")" || true
    if [[ "$before" =~ ^[0-9]+$ ]] && [[ "$after" =~ ^[0-9]+$ ]] && (( after >= before + 1 )); then
      info "Count increased for '${dtype}': ${before} -> ${after}"
      return 0
    fi
    sleep 1
  done
  warn "Count did not increase for '${dtype}' within timeout (last=$after)"
  return 1
}

test_validation_negative() {
  local payload body status
  payload='{"userKey":"","deviceType":""}'
  body="$(http_post_json "${STATS_URL}/Log/auth" "$payload" 5 || true)"
  status="${HTTP_STATUS:-0}"
  [[ "$status" == "400" ]] || { warn "Expected 400, got $status (body=$body)"; return 1; }
  [[ "$(jq -r '.message // empty' <<<"$body")" == "bad_request" ]] || { warn "Expected message=bad_request, body=$body"; return 1; }
  return 0
}

test_unknown_flow() {
  local dtype_in="MyFridge"
  local dtype_norm="Unknown"   # normalized bucket name (per service logic)
  local before after uid payload body status

  before="$(get_count_for_type "$dtype_in")" || true
  info "Baseline for '${dtype_in}' (will normalize to '${dtype_norm}'): ${before}"

  uid="smoke-$(rand_id)"
  payload=$(jq -nc --arg u "$uid" --arg d "$dtype_in" '{userKey:$u, deviceType:$d}')
  body="$(http_post_json "${STATS_URL}/Log/auth" "$payload" 5 || true)"
  status="${HTTP_STATUS:-0}"
  [[ "$status" == "200" ]] || { warn "POST /Log/auth failed: HTTP $status body=$body"; return 1; }

  # After normalization, statistics endpoint will also map query to 'Unknown'
  for _ in {1..10}; do
    after="$(get_count_for_type "$dtype_in")" || true
    if [[ "$before" =~ ^-?[0-9]+$ ]] && [[ "$after" =~ ^-?[0-9]+$ ]] && (( after >= before + 1 )); then
      info "Unknown bucket increased: ${before} -> ${after}"
      return 0
    fi
    sleep 1
  done
  warn "Unknown bucket did not increase in time (last=$after)"
  return 1
}

# ------------- Run -------------
info "Statistics base URL: ${STATS_URL}"
info "Waiting up to ${TIMEOUT}s for readiness..."
wait_until_ready

test_case "GET /livez returns 200"            test_livez
test_case "GET /startupz returns 200"         test_startupz
test_case "GET /readyz returns 200"           test_readyz
test_case "POST /Log/auth increments stats"   test_positive_flow "$DEVICE_TYPE"
test_case "POST /Log/auth validation 400"     test_validation_negative
if [[ "$RUN_UNKNOWN" -eq 1 ]]; then
  test_case "Unknown device type flow"        test_unknown_flow
else
  warn "Skipping unknown device type flow (--skip-unknown)"
fi

# ------------- Summary -------------
echo
if [[ "$FAILED" -eq 0 ]]; then
  ok "All ${TOTAL} checks passed."
  exit 0
else
  fail "${FAILED}/${TOTAL} checks failed."
  exit 1
fi
