# f1telemetry-sdk

Python SDK for the F1 Telemetry API.

## Install (local development)

```bash
pip install -e .
```

## Usage

```python
from f1telemetry_sdk import F1TelemetryClient, IngestRequest

client = F1TelemetryClient(base_url="http://localhost:8000")

client.health()

client.ingest(IngestRequest(year=2024, grand_prix="Bahrain", session_type="R"))

sessions = client.list_sessions()
session_id = sessions[0]["id"]

stats = client.session_stats(session_id)
pace = client.session_pace(session_id, window_size=5)
```
