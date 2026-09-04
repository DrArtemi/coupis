from src.biodiversity_explorer import SpeciesResolver
from src.biodiversity_explorer.gbif import GBIFOccurrenceClient

if __name__ == "__main__":
    resolver = SpeciesResolver()
    result = resolver.search(query="Grand Tetras")

    if result is None:
        raise LookupError("No matching GBIF taxon found")

    print(result)

    occurrence_client = GBIFOccurrenceClient()
    occurrence_results = occurrence_client.search(
        result.taxon_key,
        max_records=1,
    )

    print(occurrence_results)
