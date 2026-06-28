#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-https://crewai-simple-agent-12989a4f-edcc-4095-844b-30e4bea2.crewai.com}"
KICKOFF_ID="${1:-${KICKOFF_ID:-}}"

if [ -z "${CREWAI_TOKEN:-}" ]; then
  echo "CREWAI_TOKEN is required." >&2
  echo "Usage: CREWAI_TOKEN=... ./status.sh <kickoff_id>" >&2
  exit 1
fi

if [ -z "${KICKOFF_ID}" ]; then
  echo "KICKOFF_ID is required." >&2
  echo "Usage: CREWAI_TOKEN=... ./status.sh <kickoff_id>" >&2
  exit 1
fi

curl --request GET \
  --url "${BASE_URL}/status/${KICKOFF_ID}" \
  --header "Authorization: Bearer ${CREWAI_TOKEN}"
