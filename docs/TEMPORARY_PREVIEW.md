# Temporary browser preview

The frontend and API can run on one origin without a hosting account or domain.
Requires Python 3.12+ and Node.js 22+. From the downloaded repository on your Mac:

```bash
bash scripts/preview.sh
```

Open http://localhost:8080. First startup installs dependencies and downloads the
background-removal model. The preview uses its own SQLite database and uploads
under `backend/preview-data`, separate from existing application data. Stop with
Ctrl+C. To test on your phone, connect to the same Wi-Fi and open
`http://YOUR_MAC_LOCAL_IP:8080`. Allow local network access if macOS asks.

Payments and AI are disabled. Email verification is not required in this local
test mode. Seller approval rules still apply and the catalog starts empty until
approved sellers add real products. No synthetic inventory is inserted.

For an optional temporary public HTTPS URL, install Cloudflare's `cloudflared`
on your Mac and run this in another terminal:

```bash
cloudflared tunnel --url http://localhost:8080
```

Anyone with the resulting link can reach this testing application. Use test
accounts and non-sensitive photos. The URL expires when the tunnel stops. For
HTTPS-only testing set COOKIE_SECURE=true in the launcher; this disables session
cookies on local HTTP. This is a temporary testing setup, not private staging.

Cloud preview check: frontend production build passed, API health responded,
and Chromium loaded the landing page without JavaScript errors. Public tunnel
creation failed in the managed environment (outbound connection refused), so
there is no externally accessible preview link from that environment.
