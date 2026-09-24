# coupis

Python package for resolving vernacular species names through Wikidata and
GBIF, retrieving normalized GBIF occurrence records, and storing biodiversity
data in PostgreSQL/PostGIS.

## Prerequisites

- Docker with Docker Compose
- The `coupis` Conda environment with Python 3.12 or newer
- Node.js and pnpm (the web app currently uses pnpm 12)

## Initial setup

Create the local environment files from the repository root:

```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
```

Install the backend in editable mode so Python changes are available without
reinstalling:

```bash
conda run --name coupis python -m pip install -e 'apps/api[dev]'
```

Install the frontend dependencies:

```bash
cd apps/web
pnpm install
cd ../..
```

## Running the development stack

The application requires three services:

```text
Next.js :3000 -> FastAPI :8000 -> PostgreSQL/PostGIS :5432
```

GBIF and Wikidata are external APIs and do not require local services.

### 1. Start PostGIS

From the repository root:

```bash
docker compose up -d db
docker compose ps
```

Apply all database migrations after the first startup and whenever new
migrations are added:

```bash
conda run --name coupis alembic -c apps/api/alembic.ini upgrade head
```

### 2. Start FastAPI

Keep this command running in its own terminal from the repository root:

```bash
conda run --no-capture-output --name coupis \
  uvicorn coupis.api.main:app \
  --app-dir apps/api/src \
  --reload
```

Verify the API:

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/v1/species?limit=5"
curl http://localhost:8000/api/v1/regions
```

The interactive API documentation is available at
`http://localhost:8000/docs`.

### 3. Start Next.js

Keep this command running in another terminal:

```bash
cd apps/web
pnpm dev
```

Open `http://localhost:3000`. Use `localhost` consistently rather than
`127.0.0.1`, because the default API URL and CORS origin use `localhost`.

### Stopping the services

Stop FastAPI and Next.js with `Ctrl+C` in their terminals. Stop PostGIS with:

```bash
docker compose stop db
```

The database volume is retained, so the stored data remains available on the
next startup.

### Common startup problems

- `Could not load species` or `Could not load regions`: confirm FastAPI is
  responding at `http://localhost:8000/health`.
- Database connection errors: run `docker compose ps` and confirm that `db` is
  running on port 5432.
- Missing-table errors: run the Alembic upgrade command above.
- Browser CORS errors: open the web app at `http://localhost:3000` and confirm
  `NEXT_PUBLIC_API_URL=http://localhost:8000` in `apps/web/.env.local`.

## Running only the API

Start the FastAPI development server from the repository root:

```bash
conda run --no-capture-output --name coupis \
  uvicorn coupis.api.main:app \
  --app-dir apps/api/src \
  --reload
```

Open `http://localhost:8000/docs` for the interactive API documentation.

### Listing stored occurrences

`GET /api/v1/occurrences` reads occurrences from PostGIS and supports optional
filters:

```text
species_id
gbif_taxon_key
dataset_id
region_slug
region_version
bbox=west,south,east,north
observed_from
observed_until
basis_of_record
occurrence_status
country_code
limit
offset
```

For example:

```text
GET /api/v1/occurrences?gbif_taxon_key=2473577&region_slug=pyrenees&limit=100
```

The response contains `items`, `total`, `limit`, and `offset`. Region and
bounding-box filters use the PostGIS occurrence geometry.

### Listing stored species

`GET /api/v1/species` returns a paginated list of species already stored in
the database. Use `q` to search scientific, canonical, and vernacular names,
or `gbif_taxon_key` for an exact GBIF taxon:

```text
GET /api/v1/species?q=grand%20tétras&limit=20
```

Each item includes its database `id`, `gbif_taxon_key`, `scientific_name`,
`canonical_name`, and `vernacular_name`.

## Searching within a region

The PoC catalog contains coarse, non-authoritative Pyrenees and Alps
boundaries. Select a region by its stable slug and optionally pin its version:

```python
from coupis.gbif import GBIFOccurrenceClient
from coupis.services import OccurrenceSearchService

service = OccurrenceSearchService(GBIFOccurrenceClient())
gbif_occurrences = service.search(
    2473577,
    region_slug="pyrenees",
    region_version=1,
    max_records=100,
)
```

Omit `region_version` to use the latest available revision. The bundled
polygons are suitable for testing the workflow, not for scientific analysis.

## Persisting GBIF occurrences

Persist a batch inside one transaction. Species and datasets are upserted first,
then their internal IDs are used by the occurrence upsert:

```python
from coupis.db.engine import SessionFactory
from coupis.services import OccurrenceIngestionService

with SessionFactory.begin() as session:
    service = OccurrenceIngestionService.from_session(session)
    saved_occurrences = service.ingest(gbif_occurrences)
```

Repositories do not commit independently. The context commits all three batch
operations together, or rolls everything back if an operation fails.
