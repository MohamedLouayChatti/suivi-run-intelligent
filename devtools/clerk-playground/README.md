# Clerk Playground

Standalone dev sandbox — not part of the app, not built or bundled.
Purpose: sign in via a real Clerk frontend session, then mint a JWT from the
`swagger` JWT template so you can authorize requests in Swagger UI without
building a real frontend.

This exists because `authenticate_request()` validates the token's `azp`
(authorized party) claim, and that claim is only ever set by Clerk's Frontend
API based on the browser's Origin header. Tokens minted server-side via the
backend SDK (`sessions.create_token_from_template_async()`) never carry an
`azp` claim, which is what caused the `401` / `TOKEN_INVALID_AUTHORIZED_PARTIES`
error. Minting the token from an actual signed-in browser session fixes that
at the source.

## 1. Serve it

Needs a real HTTP origin — `file://` will not work with Clerk.js. From this
directory:

```bash
python3 -m http.server 5173
```

or, if you prefer:

```bash
npx serve -l 5173
```

Then open **http://localhost:5173**.

## 2. Add the origin to your backend config

Add `http://localhost:5173` to `CLERK_AUTHORIZED_PARTIES` in your backend
`.env` (as a list, not a raw string — see the gotcha below), and make sure
your `AuthenticateRequestOptions` actually reads it:

```python
authorized_parties=os.getenv("CLERK_AUTHORIZED_PARTIES", "").split(","),
```

A common gotcha: if `CLERK_AUTHORIZED_PARTIES` is read as a raw string instead
of split into a list, the whole comma-joined value becomes a single list
element and every request fails `TOKEN_INVALID_AUTHORIZED_PARTIES` even with
a valid token.

## 3. Sign in and mint a token

1. Open http://localhost:5173.
2. Sign in with a real user in your dev Clerk instance.
3. Click **Get Swagger token**. This calls
   `Clerk.session.getToken({ template: 'swagger' })` — the client-side call
   that stamps a real `azp` claim (`http://localhost:5173`) into the token.
4. Click **Copy to clipboard**.

## 4. Use it in Swagger UI

Open your FastAPI `/docs`, click **Authorize**, paste the token as the Bearer
value, and your protected routes should authenticate.

## Notes

- The `swagger` JWT template must exist in the Clerk Dashboard
  (**JWT templates** → your template). If custom claims are on your normal
  session token, mirror them in the template.
- Tokens from this template are long-lived (set in the template's Token
  Lifetime setting) — treat this like a dev credential, don't commit tokens
  anywhere.
- If you rotate your Clerk publishable key or switch instances, update the
  `data-clerk-publishable-key` attribute and both CDN `src` domains in
  `index.html` (the domain is the base64-decoded middle segment of the
  publishable key).
- No ngrok needed here — this only talks to Clerk's cloud Frontend API from
  the browser, never to your local backend, so the corporate proxy issue
  blocking your webhook tunnel doesn't apply.