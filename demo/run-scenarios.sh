#!/usr/bin/env bash
set -euo pipefail

run_case() {
  local scenario="$1"
  printf '\n=== %s ===\n' "$scenario"
  curl -sS -X POST http://localhost:8080/api/combo-bookings \
    -H 'Content-Type: application/json' \
    -d "{\"customerId\":\"CUS-01\",\"flightCode\":\"VN123\",\"hotelCode\":\"HTL-HN\",\"amount\":3500000,\"scenario\":\"$scenario\"}"
  printf '\n'
}

run_case SUCCESS
run_case HOTEL_FAIL
run_case PAYMENT_FAIL
run_case HOTEL_TIMEOUT
