# Phone bridge (remote MCP over HTTP)

Run Super on an Android phone (Termux) and let a remote AI agent call its tools.
stdio stays the default; the bridge is opt-in via `superuser --http`.

## Security model
- Binds to `127.0.0.1:8765` by default — nothing is exposed on the LAN.
- **Bearer token required** on every request (missing/wrong → `401`). Generated on first
  run at `~/.superuser/token` (mode `0600`, directory `0700`). It is never logged; the only
  log line is `Bridge token saved to <path>`. Override with `--token-file` or `SUPERUSER_TOKEN_FILE`.
- All tools still run through the Guard: approvals (`confirm=true` for HIGH risk),
  denylist, AI Defense (if enabled) and the append-only audit log.
- Rotate: delete `~/.superuser/token` and restart the bridge.

## Termux
```sh
pkg install python git cloudflared
pip install "git+https://github.com/fitzyracing1/Super@try/phone-bridge"
# terminal 1: start the bridge (creates ~/.superuser/token on first run)
AI_DEFENSE_ENABLED=false superuser --http            # --port 8765 --host 127.0.0.1
# terminal 2: outbound tunnel (no inbound ports opened on the phone)
cloudflared tunnel --url http://127.0.0.1:8765
```
cloudflared prints a `https://<random>.trycloudflare.com` URL. The MCP endpoint is
`https://<random>.trycloudflare.com/mcp`. psutil is optional on Android; without it,
system tools fall back to `/proc` / `shutil` and `list_processes` returns an empty list.

## Client configuration
- URL: `https://<random>.trycloudflare.com/mcp` (transport: streamable HTTP)
- Header: `Authorization: Bearer <contents of ~/.superuser/token>`

Example (JSON MCP client config):
```json
{"mcpServers": {"super-phone": {"type": "http",
  "url": "https://<random>.trycloudflare.com/mcp",
  "headers": {"Authorization": "Bearer ${SUPER_TOKEN}"}}}}
```
Share the token through a secret/secure field, never in chat or a committed file.
