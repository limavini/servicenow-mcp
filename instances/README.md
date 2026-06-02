# ServiceNow instances

Drop one JSON file per ServiceNow instance in this folder. The MCP's
`list_instances` / `select_instance` tools read them so you can switch the active
instance at runtime (the agent asks which one to use).

- **Real credential files (`*.json`) are gitignored** — they never get committed.
- Only this `README.md` and `*.example.json` templates are tracked.
- Override this folder's location with the `SERVICENOW_INSTANCES_DIR` env var.

## File format

Copy `instance.example.json` to `<name>.json` and fill it in. The file name (minus
`.json`) is the instance name unless you set `"name"` explicitly.

Basic auth:
```json
{
  "name": "dev185907",
  "instance_url": "https://dev185907.service-now.com",
  "auth_type": "basic",
  "username": "admin",
  "password": "your-password"
}
```

OAuth: `"auth_type": "oauth"` with `client_id`, `client_secret`, `username`,
`password` (and optional `token_url`).

API key: `"auth_type": "api_key"` with `api_key` (and optional `api_key_header`).

## Usage

In Claude, before doing instance work: `list_instances` → pick one → `select_instance`.
The `servicenow-story-builder` skill does this automatically as its first step.
