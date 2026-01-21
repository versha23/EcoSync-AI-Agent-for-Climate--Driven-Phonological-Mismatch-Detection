"""
Test Qdrant queries 
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import pandas as pd

print("🔍 TESTING QDRANT SEMANTIC SEARCH")
print("="*70)

# Initialize
client = QdrantClient("localhost", port=6333)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

def semantic_search(query_text, collection_name='observations', limit=5, filters=None):
    """Perform semantic search"""
    
    
    query_vector = embedder.encode(query_text).tolist()
    
   
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=limit,
        query_filter=filters
    )
    
    return results.points  

def print_results(results, title):
    """Pretty print search results"""
    print(f"\n{'='*70}")
    print(f"🔍 QUERY: {title}")
    print(f"{'='*70}")
    
    if not results:
        print("  ⚠️  No results found")
        return
    
    for i, hit in enumerate(results, 1):
        print(f"\n  [{i}] Score: {hit.score:.3f}")
        print(f"      {hit.payload.get('text_description', 'No description')}")
        print(f"      Species: {hit.payload.get('species_common', 'N/A')}")
        print(f"      Date: {hit.payload.get('observed_date', 'N/A')[:10] if hit.payload.get('observed_date') else 'N/A'}")
        print(f"      Day of Year: {hit.payload.get('day_of_year', 'N/A')}")



print("\n🎯 Running test queries...\n")

# Query 1: Find butterfly observations in spring
print("\n" + "▶"*35)
results = semantic_search(
    "butterfly emergence in spring season March April",
    limit=5,
    filters=Filter(
        must=[
            FieldCondition(key="species_type", match=MatchValue(value="butterfly"))
        ]
    )
)
print_results(results, "Butterfly emergence in spring")

# Query 2: Find mango flowering events
print("\n" + "▶"*35)
results = semantic_search(
    "mango tree flowering blooming",
    limit=5
)
print_results(results, "Mango flowering events")

# Query 3: Find bee activity in 2024
print("\n" + "▶"*35)
results = semantic_search(
    "bee pollination activity foraging",
    limit=5,
    filters=Filter(
        must=[
            FieldCondition(key="year", match=MatchValue(value=2024))
        ]
    )
)
print_results(results, "Bee activity in 2024")

# Query 4: Climate patterns during pre-monsoon
print("\n" + "▶"*35)
results = semantic_search(
    "temperature warming pre-monsoon March April May",
    collection_name='climate_data',
    limit=5
)
print(f"\n{'='*70}")
print(f"🔍 QUERY: Climate patterns during pre-monsoon")
print(f"{'='*70}")

for i, hit in enumerate(results, 1):
    print(f"\n  [{i}] Score: {hit.score:.3f}")
    print(f"      {hit.payload.get('text_description', 'No description')}")
    temp_anom = hit.payload.get('temperature_anomaly')
    if temp_anom is not None:
        print(f"      Temp Anomaly: {temp_anom:+.2f}°C")

# Query 5: Phenological shifts
print("\n" + "▶"*35)
results = semantic_search(
    "species shifted earlier timing phenology",
    collection_name='temporal_patterns',
    limit=10
)
print(f"\n{'='*70}")
print(f"🔍 QUERY: Species with phenological shifts")
print(f"{'='*70}")

for i, hit in enumerate(results, 1):
    shift_days = hit.payload.get('shift_days')
    baseline_doy = hit.payload.get('baseline_median_doy')
    current_doy = hit.payload.get('current_median_doy')
    
    print(f"\n  [{i}] {hit.payload.get('species', 'Unknown')}")
    if shift_days is not None:
        print(f"      Shift: {shift_days:.1f} days {hit.payload.get('shift_direction', 'N/A')}")
    if baseline_doy is not None:
        print(f"      Baseline DOY: {baseline_doy:.0f}")
    if current_doy is not None:
        print(f"      Current DOY: {current_doy:.0f}")

# Query 6: Species relationships
print("\n" + "▶"*35)
results = semantic_search(
    "butterfly depends on plant leaves",
    collection_name='species_metadata',
    limit=3
)
print(f"\n{'='*70}")
print(f"🔍 QUERY: Species dependency relationships")
print(f"{'='*70}")

for i, hit in enumerate(results, 1):
    print(f"\n  [{i}] Score: {hit.score:.3f}")
    print(f"      {hit.payload.get('text_description', 'No description')}")

# Query 7: Find temporal mismatches
print("\n" + "▶"*35)
print(f"\n{'='*70}")
print(f"🔍 ADVANCED QUERY: Detect Temporal Mismatches")
print(f"{'='*70}")

# Get Giant Honey Bee observations in 2024
bee_results = semantic_search(
    "Giant Honey Bee activity",
    limit=200,
    filters=Filter(
        must=[
            FieldCondition(key="species_common", match=MatchValue(value="Giant Honey Bee")),
            FieldCondition(key="year", match=MatchValue(value=2024))
        ]
    )
)

# Get Mango observations in 2024
mango_results = semantic_search(
    "Mango flowering",
    limit=200,
    filters=Filter(
        must=[
            FieldCondition(key="species_common", match=MatchValue(value="Mango")),
            FieldCondition(key="year", match=MatchValue(value=2024))
        ]
    )
)

if bee_results and mango_results:
    bee_doys = [r.payload['day_of_year'] for r in bee_results if 'day_of_year' in r.payload]
    mango_doys = [r.payload['day_of_year'] for r in mango_results if 'day_of_year' in r.payload]
    
    if bee_doys and mango_doys:
        bee_median = pd.Series(bee_doys).median()
        mango_median = pd.Series(mango_doys).median()
        
        gap = bee_median - mango_median
        
        print(f"\n  🐝 Giant Honey Bee 2024: Median DOY {bee_median:.0f} ({len(bee_doys)} observations)")
        print(f"  🌳 Mango flowering 2024: Median DOY {mango_median:.0f} ({len(mango_doys)} observations)")
        print(f"  ⚠️  TEMPORAL GAP: {gap:.0f} days")
        
        if gap > 10:
            print(f"\n  🚨 MISMATCH DETECTED!")
            print(f"      Bees arrive {gap:.0f} days AFTER mango flowers peak")
            print(f"      This indicates poor pollination synchrony")
        elif gap < -10:
            print(f"\n  🚨 MISMATCH DETECTED!")
            print(f"      Bees arrive {abs(gap):.0f} days BEFORE mango flowers")
            print(f"      This indicates bees miss optimal flowering window")
        else:
            print(f"\n  ✅ Good synchrony (gap < 10 days)")
    else:
        print("\n  ⚠️  Insufficient data for mismatch calculation")
else:
    print("\n  ⚠️  No data found for mismatch analysis")

print("\n" + "="*70)
print("✅ QUERY TESTS COMPLETE!")
