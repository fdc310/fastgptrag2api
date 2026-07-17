# FastGPT RAG API Wrapper

A FastAPI wrapper around FastGPT knowledge base OpenAPI, adding device-name based dataset resolution and ownership verification.

## Architecture

```
Client  --Bearer AES token (device_name inside)-->  This API  --Bearer token-->  FastGPT
                                                          |
                                                  MySQL (ya_setting_robot / ya_member_robot_attributes)
```

- The AES token carries `device_name`, which resolves to a device in the `ya_setting_robot` table
- The device's `dataset_id` is looked up from `ya_member_robot_attributes`
- All subsequent operations verify ownership before forwarding to FastGPT
- Results are cached in memory for 5 minutes

## Setup

```bash
uv sync
cp .env.example .env
# edit .env with your FastGPT URL, API keys, and MySQL credentials
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Or with Docker:

```bash
docker compose up -d
```

## Authentication

All endpoints except `/health` require a single header:

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <AES_TOKEN>`, an AES-256-CBC encrypted token carrying `device_name` + `timestamp` |

The token plaintext is `{"device_name": "...", "timestamp": ...}`, encrypted as `base64url(IV[16] + ciphertext)`. The server decrypts it with `AES_SECRET_KEY` (from `.env`) and rejects tokens older than `AES_TOKEN_TTL` (default 300s).

Generate a token with the bundled script:

```bash
python scripts/generate_token.py <device_name>
```

## API Endpoints

### Health

| Method | Path | Description |
|---|---|---|
| GET | /health | Health check (no auth required) |

### Datasets

| Method | Path | Description |
|---|---|---|
| GET | /datasets | Get dataset detail for the resolved device |

### Collections

| Method | Path | Description |
|---|---|---|
| POST | /collections/list | List collections in the dataset |
| GET | /collections/{collection_id} | Get collection detail (ownership verified) |
| POST | /collections/update | Update collection |

### Data

| Method | Path | Description |
|---|---|---|
| POST | /collections/{collection_id}/data/push | Push data to collection |
| POST | /collections/{collection_id}/data/list | List data in collection |
| GET | /collections/{collection_id}/data/{data_id} | Get data detail |
| PUT | /collections/{collection_id}/data/update | Update data |
| DELETE | /collections/{collection_id}/data/{data_id} | Delete data |

### Search

| Method | Path | Description |
|---|---|---|
| POST | /search | Search in the resolved dataset |

## Database Tables (read-only)

The following existing MySQL tables are queried (not created by this service):

- `ya_setting_robot` — device registry (key columns: `id`, `device_name`, `is_delete`)
- `ya_member_robot_attributes` — device-to-dataset binding (key columns: `id`, `robot_id`, `dataset_id`, `member_id`, `is_delete`)

## Configuration

See `.env.example` for all environment variables.
