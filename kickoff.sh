#!/usr/bin/env sh
set -eu

BASE_URL="${BASE_URL:-https://crewai-simple-agent-24ffba2f-5065-4819-9f2d-d6a50318.crewai.com}"
TOPIC="${TOPIC:-Briga entre Flow Podcast e Monark}"

if [ -z "${CREWAI_TOKEN:-}" ]; then
  echo "CREWAI_TOKEN is required." >&2
  echo "Usage: CREWAI_TOKEN=... [TOPIC=...] [RESTORE_FROM_STATE_ID=...] ./kickoff.sh" >&2
  exit 1
fi

PAYLOAD="$(python3 - <<'PY'
import json
import os

payload = {"inputs": {"topic": os.environ["TOPIC"]}}
restore_from_state_id = os.getenv("RESTORE_FROM_STATE_ID")

if restore_from_state_id:
    payload["restoreFromStateId"] = restore_from_state_id

print(json.dumps(payload))
PY
)"

curl --request POST \
  --url "${BASE_URL}/kickoff" \
  --header "Authorization: Bearer ${CREWAI_TOKEN}" \
  --header "Content-Type: application/json" \
  --data "${PAYLOAD}"
