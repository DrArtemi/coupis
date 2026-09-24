# coupis web

Next.js frontend for exploring biodiversity occurrences by species and region.
The complete PostGIS, FastAPI, and web startup sequence is documented in the
[root README](../../README.md).

## Initial setup

From `apps/web`:

```bash
cp .env.example .env.local
pnpm install
```

The default API configuration is:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development

Start FastAPI first, then run:

```bash
pnpm dev
```

Open `http://localhost:3000`.

Useful checks:

```bash
pnpm typecheck
pnpm lint
pnpm build
```

## Regenerating the API types

After changing a FastAPI route or response model, export the OpenAPI schema
from the repository root:

```bash
conda run --name coupis python \
  apps/api/scripts/export_openapi.py contracts/openapi.json
```

Then regenerate the TypeScript declarations:

```bash
cd apps/web
pnpm generate:api
```

The generated declarations live in `src/generated/api-schema.d.ts`. Do not
edit that file manually.
