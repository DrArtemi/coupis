from coupis import SpeciesResolver
from coupis.db.engine import SessionFactory
from coupis.gbif import GBIFOccurrenceClient
from coupis.services.occurrence_ingestion import OccurrenceIngestionService
from coupis.services.occurrence_search import OccurrenceSearchService

if __name__ == "__main__":
    resolver = SpeciesResolver()
    result = resolver.search(query="Grand Tetras")

    if result is None:
        raise LookupError("No matching GBIF taxon found")


    occurrence_service = OccurrenceSearchService(gbif_client=GBIFOccurrenceClient())
    occurrence_results = occurrence_service.search(
        result.taxon_key,
        region_slug="pyrenees",
        region_version=1,
        max_records=100
    )

    with SessionFactory.begin() as session:
        occurrence_ingestion_service = OccurrenceIngestionService.from_session(session)
        res = occurrence_ingestion_service.ingest(occurrence_results)
