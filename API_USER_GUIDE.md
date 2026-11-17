# Marketo Bulk Activity API Simulator — API Documentation & User Guide

A complete, production-grade guide for consuming the **Marketo Bulk Activity Export API Simulator** (Activity Type 2: *Fill Out Form*).

---

## 1. Quick Reference & Base URLs

| Environment | Base URL | Interactive Swagger Docs | OpenAPI Schema |
| :--- | :--- | :--- | :--- |
| **Production (Vercel Global Edge)** | `https://marketo-api-simulator.vercel.app` | [Swagger UI](https://marketo-api-simulator.vercel.app/docs) | [`/openapi.json`](https://marketo-api-simulator.vercel.app/openapi.json) |
| **Local Development** | `http://localhost:8000` | [`/docs`](http://localhost:8000/docs) | [`/openapi.json`](http://localhost:8000/openapi.json) |

### Default Credentials
* **Client ID**: `marketo-poc-client`
* **Client Secret**: `change-me`
* **Grant Type**: `client_credentials`
* **Token TTL**: 3,599 seconds (1 hour)

---

## 2. API Workflow Sequence

The simulator implements the asynchronous 5-step Marketo Bulk Activity lifecycle:

```mermaid
sequenceDiagram
    autonumber
    actor Client as ETL / Databricks Client
    participant Auth as POST /identity/oauth/token
    participant Create as POST /create.json
    participant Enqueue as POST /enqueue.json
    participant Status as GET /status.json
    participant File as GET /file.json

    Client->>Auth: Request Bearer Token (client_credentials)
    Auth-->>Client: 200 OK: access_token, expires_in=3599

    Client->>Create: Filter startAt, endAt, activityTypeIds=[2]
    Create-->>Client: 200 OK: exportId, status="Created"

    Client->>Enqueue: Enqueue export job by exportId
    Enqueue-->>Client: 200 OK: status="Queued"

    loop Poll every 2-3 seconds until Completed
        Client->>Status: Check job status
        Status-->>Client: status="Queued" | "Processing" | "Completed"
    end

    Client->>File: Download TSV file
    File-->>Client: 200 OK: 21-column TSV bytes (Content-Type: text/tab-separated-values)
```

---

## 3. Detailed Endpoint Reference

### Step 1: Obtain Access Token
* **Method**: `POST`
* **Path**: `/identity/oauth/token`
* **Content-Type**: `application/x-www-form-urlencoded`

#### Request Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `grant_type` | string | Yes | Must be `client_credentials` |
| `client_id` | string | Yes | Your configured client ID (e.g. `marketo-poc-client`) |
| `client_secret` | string | Yes | Your configured client secret (e.g. `change-me`) |

#### Example Request (cURL)
```bash
curl -X POST "https://marketo-api-simulator.vercel.app/identity/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=marketo-poc-client&client_secret=change-me"
```

#### Example Response (HTTP 200)
```json
{
  "access_token": "uPIMSjwKLgjppW1FpFQMyaP7z4FD-fLtcgNdaKWnSV4",
  "token_type": "bearer",
  "expires_in": 3599,
  "scope": "marketo.mock.api"
}
```

---

### Step 2: Create Export Job
* **Method**: `POST`
* **Path**: `/bulk/v1/activities/export/create.json`
* **Headers**: 
  - `Authorization: Bearer <access_token>`
  - `Content-Type: application/json`

#### Validation Rules
1. `activityTypeIds`: Must contain **only** integer `[2]` (*Fill Out Form*).
2. `startAt` and `endAt`: Must be ISO-8601 strings with timezone indicators (e.g. `Z`).
3. `startAt` must be strictly earlier than `endAt`.
4. Inclusive date range must not exceed **30 days**. Formula: `(UTC_date(endAt) - UTC_date(startAt)).days + 1 <= 30`.
5. Strict schema validation: unexpected fields (e.g. `"format"`) are **rejected** with HTTP 422.

#### Example Request Body
```json
{
  "filter": {
    "createdAt": {
      "startAt": "2026-11-01T00:00:00Z",
      "endAt": "2026-11-06T23:59:59Z"
    },
    "activityTypeIds": [2]
  }
}
```

#### Example Response (HTTP 200)
```json
{
  "requestId": "32343a96-f920-4d99-a1f5-7763d04ac633",
  "success": true,
  "result": [
    {
      "exportId": "c4febe83-8218-40b4-891e-a7dc9fef71f3",
      "status": "Created",
      "createdAt": "2026-11-17T02:19:00Z",
      "queuedAt": null,
      "startedAt": null,
      "finishedAt": null,
      "format": "TSV",
      "numberOfDays": null,
      "numberOfRecords": null,
      "fileSize": null,
      "fileChecksum": null
    }
  ]
}
```

---

### Step 3: Enqueue Export Job
* **Method**: `POST`
* **Path**: `/bulk/v1/activities/export/{exportId}/enqueue.json`
* **Headers**: `Authorization: Bearer <access_token>`

#### Rules
- Transitions status from `Created` -> `Queued`.
- Enforces maximum active queue concurrency limit ($\le 10$ active jobs).
- Sets deterministic delays: **2 seconds** in Queue, **5 seconds** in Processing.

#### Example Response (HTTP 200)
```json
{
  "requestId": "442947cc-4bf5-4793-9981-42cd684c72f2",
  "success": true,
  "result": [
    {
      "exportId": "c4febe83-8218-40b4-891e-a7dc9fef71f3",
      "status": "Queued",
      "createdAt": "2026-11-17T02:19:00Z",
      "queuedAt": "2026-11-17T02:19:10Z",
      "startedAt": null,
      "finishedAt": null,
      "format": "TSV"
    }
  ]
}
```

---

### Step 4: Poll Export Job Status
* **Method**: `GET`
* **Path**: `/bulk/v1/activities/export/{exportId}/status.json`
* **Headers**: `Authorization: Bearer <access_token>`

#### Lifecycle States
- `Created`: Registered in database, not enqueued.
- `Queued`: In queue (first 2 seconds after enqueue).
- `Processing`: Synthesizing dataset (next 5 seconds).
- `Completed`: File ready for download; includes deterministic `numberOfRecords`, `fileSize`, and `fileChecksum`.

#### Example Response When Completed (HTTP 200)
```json
{
  "requestId": "60eb4c6c-603f-441e-bc5b-24e06eb1def2",
  "success": true,
  "result": [
    {
      "exportId": "c4febe83-8218-40b4-891e-a7dc9fef71f3",
      "status": "Completed",
      "createdAt": "2026-11-17T02:19:00Z",
      "queuedAt": "2026-11-17T02:19:10Z",
      "startedAt": "2026-11-17T02:19:12Z",
      "finishedAt": "2026-11-17T02:19:17Z",
      "format": "TSV",
      "numberOfDays": 6,
      "numberOfRecords": 23,
      "fileSize": 26984,
      "fileChecksum": "sha256:4bcee4cbc52c4b1e9e689effbbc4b6ea663c75b50fe76690cec5c4bbe192f6b8"
    }
  ]
}
```

---

### Step 5: Download TSV Source File
* **Method**: `GET`
* **Path**: `/bulk/v1/activities/export/{exportId}/file.json`
* **Headers**: `Authorization: Bearer <access_token>`

> [!NOTE]
> Even though the URL ends in `file.json` for Marketo API compatibility, the actual response is a raw **TSV file** stream.

#### Response Headers
- `Content-Type`: `text/tab-separated-values; charset=utf-8`
- `Content-Disposition`: `attachment; filename="marketo_fillout_form_<exportId>.tsv"`
- `X-Checksum-SHA256`: `4bcee4cbc52c4b1e9e689effbbc4b6ea663c75b50fe76690cec5c4bbe192f6b8`
- `X-Record-Count`: `23`

---

## 4. TSV File Schema (Exact 21 Columns)

The downloaded TSV contains **exactly 21 columns** separated by horizontal tab characters (`\t`) and terminated with Unix newlines (`\n`):

| # | Column Name | Format / Example | Description |
| :---: | :--- | :--- | :--- |
| **1** | `marketoGUID` | `86066334` | Unique numeric identifier for activity record |
| **2** | `leadId` | `852780` | Synthetic lead pool ID (100000 - 999999) |
| **3** | `activityDate` | `2026-11-01T07:49:40Z` | UTC ISO-8601 timestamp within range |
| **4** | `activityTypeId` | `2` | Fill Out Form activity ID |
| **5** | `primaryAttributeValueId` | `1029` or `1356` | 80% weight `1029`, 20% weight `1356` |
| **6** | `primaryAttributeValue` | `AEM·Form·Testing.AEM·Form·Testing` | Form testing name |
| **7** | `CAPTCHANormalizedScore` | *Empty* | Null (represented as empty tab field) |
| **8** | `CAPTCHAProvider` | *Empty* | Null (represented as empty tab field) |
| **9** | `CAPTCHARawScore` | *Empty* | Null (represented as empty tab field) |
| **10** | `ClientIPAddress` | `203.0.113.19` or *Empty* | RFC 5737 documentation IP for standard forms |
| **11** | `FormFields` | `a:10:{s:13:"mRFSFirstName";s:4:"Zeta";...}` | PHP-serialized associative array |
| **12** | `mRFSBrand` | `BT` or *Empty* | Brand identifier |
| **13** | `mRFSConsentChannel` | *Empty* | Empty tab field |
| **14** | `mRFSConsentType` | *Empty* | Empty tab field |
| **15** | `mRFSCountry` | *Empty* | Empty tab field |
| **16** | `ProgramName` | *Empty* | Empty tab field |
| **17** | `ProgramType` | *Empty* | Empty tab field |
| **18** | `QueryParameters` | `{}` or `utm_source=...` | Literal JSON `{}` or UTM query string |
| **19** | `ReferrerURL` | `https://business.example.test/...` | Synthetic safe test URL |
| **20** | `UserAgent` | `Mozilla/5.0...` or *Empty* | Realistic browser user agent |
| **21** | `WebpageID` | `18420` | Landing webpage ID |

### Top-Level Null vs Internal FormFields Null
1. **Top-level TSV Nulls**: Written as **empty fields between tabs** (e.g. `colA\t\tcolC`). Never written as literal `"Null"`.
2. **FormFields Nulls**: Written in PHP serialization format as **`N;`** (e.g. `s:9:"eventDate";N;`).

---

## 5. Ready-to-Run Code Examples

### A. Python (`requests` / Databricks Notebook)

```python
import time
import requests
import hashlib

BASE_URL = "https://marketo-api-simulator.vercel.app"
CLIENT_ID = "marketo-poc-client"
CLIENT_SECRET = "change-me"

# 1. Obtain Bearer Token
token_res = requests.post(
    f"{BASE_URL}/identity/oauth/token",
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    },
)
token_res.raise_for_status()
access_token = token_res.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print("Authenticated successfully.")

# 2. Create TSV Export Job
create_res = requests.post(
    f"{BASE_URL}/bulk/v1/activities/export/create.json",
    headers=headers,
    json={
        "filter": {
            "createdAt": {
                "startAt": "2026-11-01T00:00:00Z",
                "endAt": "2026-11-06T23:59:59Z",
            },
            "activityTypeIds": [2],
        }
    },
)
create_res.raise_for_status()
export_id = create_res.json()["result"][0]["exportId"]
print(f"Created Export ID: {export_id}")

# 3. Enqueue Export Job
requests.post(
    f"{BASE_URL}/bulk/v1/activities/export/{export_id}/enqueue.json",
    headers=headers,
).raise_for_status()
print("Job enqueued. Waiting for completion...")

# 4. Poll Status Until Completed
while True:
    status_res = requests.get(
        f"{BASE_URL}/bulk/v1/activities/export/{export_id}/status.json",
        headers=headers,
    )
    status_data = status_res.json()["result"][0]
    status = status_data["status"]
    print(f"  Current status: {status}")
    if status == "Completed":
        records = status_data["numberOfRecords"]
        expected_checksum = status_data["fileChecksum"]
        break
    time.sleep(2)

# 5. Download and Verify TSV File
file_res = requests.get(
    f"{BASE_URL}/bulk/v1/activities/export/{export_id}/file.json",
    headers=headers,
)
file_res.raise_for_status()
tsv_bytes = file_res.content

# Verify SHA-256 Checksum
actual_hash = "sha256:" + hashlib.sha256(tsv_bytes).hexdigest()
assert actual_hash == expected_checksum, "Checksum mismatch!"
print(f"Downloaded {len(tsv_bytes):,} bytes ({records} records). Checksum verified!")

# Save to local file
filename = f"marketo_fillout_form_{export_id}.tsv"
with open(filename, "wb") as f:
    f.write(tsv_bytes)
print(f"Saved TSV file: {filename}")
```

---

### B. Databricks PySpark Integration (Direct Ingestion into Delta Lake)

```python
# Databricks Notebook cell
import io
import time
import requests
import pandas as pd

BASE_URL = "https://marketo-api-simulator.vercel.app"
AUTH = {"grant_type": "client_credentials", "client_id": "marketo-poc-client", "client_secret": "change-me"}

# Authenticate & Enqueue
token = requests.post(f"{BASE_URL}/identity/oauth/token", data=AUTH).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

job = requests.post(
    f"{BASE_URL}/bulk/v1/activities/export/create.json",
    headers=headers,
    json={"filter": {"createdAt": {"startAt": "2026-11-01T00:00:00Z", "endAt": "2026-11-06T23:59:59Z"}, "activityTypeIds": [2]}}
).json()["result"][0]["exportId"]

requests.post(f"{BASE_URL}/bulk/v1/activities/export/{job}/enqueue.json", headers=headers)

# Poll until Completed
while requests.get(f"{BASE_URL}/bulk/v1/activities/export/{job}/status.json", headers=headers).json()["result"][0]["status"] != "Completed":
    time.sleep(2)

# Fetch TSV
raw_tsv = requests.get(f"{BASE_URL}/bulk/v1/activities/export/{job}/file.json", headers=headers).content

# Load into Spark DataFrame
pdf = pd.read_csv(io.BytesIO(raw_tsv), sep="\t", dtype=str)
df = spark.createDataFrame(pdf)

display(df)

# Write to Bronze Delta Lake Table
# df.write.format("delta").mode("append").saveAsTable("bronze_marketo_activities")
```

---

### C. Complete Bash / cURL 1-Liner Workflow

```bash
#!/bin/bash
set -e

BASE_URL="https://marketo-api-simulator.vercel.app"

echo "1. Getting token..."
TOKEN=$(curl -s -X POST "${BASE_URL}/identity/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=marketo-poc-client&client_secret=change-me" \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "2. Creating export job..."
EXPORT_ID=$(curl -s -X POST "${BASE_URL}/bulk/v1/activities/export/create.json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"filter":{"createdAt":{"startAt":"2026-11-01T00:00:00Z","endAt":"2026-11-06T23:59:59Z"},"activityTypeIds":[2]}}' \
  | grep -o '"exportId":"[^"]*' | cut -d'"' -f4)
echo "   Export ID: ${EXPORT_ID}"

echo "3. Enqueueing job..."
curl -s -X POST "${BASE_URL}/bulk/v1/activities/export/${EXPORT_ID}/enqueue.json" \
  -H "Authorization: Bearer ${TOKEN}" > /dev/null

echo "4. Polling status..."
while true; do
  STATUS=$(curl -s "${BASE_URL}/bulk/v1/activities/export/${EXPORT_ID}/status.json" \
    -H "Authorization: Bearer ${TOKEN}" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  echo "   Status: ${STATUS}"
  if [ "$STATUS" == "Completed" ]; then break; fi
  sleep 2
done

echo "5. Downloading TSV file..."
curl -s "${BASE_URL}/bulk/v1/activities/export/${EXPORT_ID}/file.json" \
  -H "Authorization: Bearer ${TOKEN}" \
  -o "marketo_fillout_form_${EXPORT_ID}.tsv"

echo "Done! File saved: marketo_fillout_form_${EXPORT_ID}.tsv"
head -n 2 "marketo_fillout_form_${EXPORT_ID}.tsv"
```

---

## 6. Marketo Error Code Reference

The simulator uses standard Marketo error envelopes:

```json
{
  "requestId": "f8697f43-e480-44a1-82c0-2cdfb936457a",
  "success": false,
  "errors": [
    {
      "code": "1005",
      "message": "Unsupported activity type filter: [1]"
    }
  ]
}
```

| HTTP Status | Marketo Code | Trigger Condition / Description |
| :---: | :---: | :--- |
| **401** | `601` | Missing, expired, malformed, or invalid Bearer access token |
| **422** | `1003` | Invalid date range (`startAt` not earlier than `endAt`, or range $> 30$ days) |
| **422** | `1005` | Unsupported activity type filter (e.g. `[1]` instead of `[2]`) |
| **422** | `1029` | Too many active jobs in queue (concurrency limit $> 10$) |
| **404** | `1034` | Export job ID not found |
| **409** | `1035` | Job already enqueued (cannot enqueue a job twice) |
| **409** | `1036` | File requested before job reached `Completed` state |
| **422** | `1040` | Request validation error (e.g. unrecognized parameters, missing required fields) |
| **422** | `1041` | Total calculated records exceeded maximum limit |

---

## 7. Health & Monitoring Endpoints

* **Liveness Probe**: `GET /health/live`
  - Returns `{"status": "ok"}` with HTTP 200.
* **Readiness Probe**: `GET /health/ready`
  - Verifies database connectivity and returns `{"status": "ok", "database": "connected"}`.
