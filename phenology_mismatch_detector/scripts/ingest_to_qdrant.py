"""
 cleaned phenology data into Qdrant vector database
"""
import pandas as pd
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import hashlib

print("🚀 INGESTING DATA INTO QDRANT")
print("="*70)


print("\n🔗 Connecting to Qdrant...")
client = QdrantClient("localhost", port=6333)
print("✅ Connected!")


print("\n🤖 Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded!")


COLLECTIONS = {
    'observations': {
        'description': 'All species observations with temporal metadata',
        'vector_size': 384  # all-MiniLM-L6-v2 produces 384-dim vectors
    },
    'climate_data': {
        'description': 'Climate signals (temperature, rainfall)',
        'vector_size': 384
    },
    'species_metadata': {
        'description': 'Species information and relationships',
        'vector_size': 384
    },
    'temporal_patterns': {
        'description': 'Baseline vs current phenological patterns',
        'vector_size': 384
    }
}

def create_collections():
    """Create or recreate Qdrant collections"""
    print("\n📦 Creating Qdrant collections...")
    
    for collection_name, config in COLLECTIONS.items():
        
        try:
            client.delete_collection(collection_name)
            print(f"  🗑️  Deleted existing '{collection_name}'")
        except:
            pass
        
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=config['vector_size'],
                distance=Distance.COSINE
            )
        )
        print(f"  ✅ Created '{collection_name}' - {config['description']}")

def generate_observation_text(row):
    
    text = (
        f"{row['species_common']} ({row['species_type']}) "
        f"observed on {row['observed_date'].strftime('%B %d, %Y')} "
        f"(day {row['day_of_year']} of {row['year']}) "
        f"in {row.get('place_guess', 'Karnataka')} "
        f"during {row['season']} season"
    )
    return text

def ingest_observations():
    
    print("\n📥 Ingesting observations...")
    
    # Load combined data
    df = pd.read_csv('data/processed/all_species_combined.csv')
    df['observed_date'] = pd.to_datetime(df['observed_date'])
    
    print(f"  📊 Total observations to ingest: {len(df):,}")
    
    points = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="  Processing"):
       
        text = generate_observation_text(row)
        
        
        vector = embedder.encode(text).tolist()
        
        
        point_id = int(hashlib.md5(str(row['observation_id']).encode()).hexdigest()[:16], 16) % (10**9)
        
       
        payload = {
            'observation_id': int(row['observation_id']),
            'species_key': row['species_key'],
            'species_common': row['species_common'],
            'species_type': row['species_type'],
            'species_role': row['species_role'],
            'observed_date': row['observed_date'].isoformat(),
            'year': int(row['year']),
            'month': int(row['month']),
            'day_of_year': int(row['day_of_year']),
            'season': row['season'],
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'place': row.get('place_guess', 'Karnataka'),
            'text_description': text
        }
        
        # Create point
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        
        points.append(point)
        
        
        if len(points) >= 100:
            client.upsert(
                collection_name='observations',
                points=points
            )
            points = []
    
   
    if points:
        client.upsert(
            collection_name='observations',
            points=points
        )
    
    print(f"  ✅ Ingested {len(df):,} observations")

def ingest_climate_data():
    
    print("\n Ingesting climate data...")
    
    
    df = pd.read_csv('data/raw/karnataka_climate_monthly.csv')
    
    print(f"  📊 Climate records to ingest: {len(df):,}")
    
    points = []
    
    for idx, row in tqdm(df.iterrows(), total=len(df), desc="  Processing"):
        
        text = (
            f"Karnataka climate in {row['year']}-{row['month']:02d}: "
            f"temperature {row['temperature_mean']:.1f}°C "
            f"(anomaly: {row['temperature_anomaly']:+.2f}°C), "
            f"rainfall {row['rainfall_mm']:.1f}mm, "
            f"season {row['season']}"
        )
        
        
        vector = embedder.encode(text).tolist()
        
        
        point_id = int(row['year']) * 100 + int(row['month'])
        
        
        payload = {
            'year': int(row['year']),
            'month': int(row['month']),
            'temperature_mean': float(row['temperature_mean']),
            'temperature_max': float(row['temperature_max']),
            'temperature_min': float(row['temperature_min']),
            'temperature_anomaly': float(row['temperature_anomaly']),
            'rainfall_mm': float(row['rainfall_mm']),
            'season': row['season'],
            'text_description': text
        }
        
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        
        points.append(point)
    
    client.upsert(
        collection_name='climate_data',
        points=points
    )
    
    print(f"  ✅ Ingested {len(df):,} climate records")

def ingest_phenology_patterns():
    
    print("\n📊 Ingesting phenological patterns...")
    
    
    df = pd.read_csv('data/processed/phenology_summary.csv')
    
    points = []
    point_id = 1
    
    for idx, row in df.iterrows():
        
        shift_direction = "earlier" if row['shift_days'] < 0 else "later"
        shift_magnitude = abs(row['shift_days'])
        
        text = (
            f"{row['species']} ({row['type']}) phenology: "
            f"baseline median day {row['baseline_median_doy']:.0f}, "
            f"current median day {row['current_median_doy']:.0f}, "
            f"shifted {shift_magnitude:.1f} days {shift_direction}"
        )
        
        
        vector = embedder.encode(text).tolist()
        
    
        payload = {
            'species': row['species'],
            'species_type': row['type'],
            'total_observations': int(row['total_obs']),
            'baseline_median_doy': float(row['baseline_median_doy']) if pd.notna(row['baseline_median_doy']) else None,
            'current_median_doy': float(row['current_median_doy']) if pd.notna(row['current_median_doy']) else None,
            'shift_days': float(row['shift_days']) if pd.notna(row['shift_days']) else None,
            'shift_direction': shift_direction,
            'text_description': text
        }
        
        point = PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
        
        points.append(point)
        point_id += 1
    
    client.upsert(
        collection_name='temporal_patterns',
        points=points
    )
    
    print(f"  ✅ Ingested {len(df):,} phenological patterns")

def ingest_species_metadata():
    
    print("\n🔗 Ingesting species metadata...")
    
    
    relationships = [
        {
            'consumer': 'Common Mormon',
            'consumer_type': 'butterfly_larvae',
            'resource': 'Curry Leaf',
            'resource_type': 'host_plant',
            'relationship': 'obligate_herbivory',
            'description': 'Common Mormon butterfly larvae feed exclusively on Curry Leaf fresh foliage'
        },
        {
            'consumer': 'Asian Honey Bee',
            'consumer_type': 'pollinator',
            'resource': 'Mango',
            'resource_type': 'flower',
            'relationship': 'pollination',
            'description': 'Asian Honey Bee pollinates Mango flowers for nectar and pollen'
        },
        {
            'consumer': 'Giant Honey Bee',
            'consumer_type': 'pollinator',
            'resource': 'Mango',
            'resource_type': 'flower',
            'relationship': 'pollination',
            'description': 'Giant Honey Bee pollinates Mango flowers'
        },
        {
            'consumer': 'Plain Tiger',
            'consumer_type': 'butterfly_adult',
            'resource': 'Lantana',
            'resource_type': 'nectar_source',
            'relationship': 'nectarivory',
            'description': 'Plain Tiger butterfly drinks nectar from Lantana flowers'
        },
        {
            'consumer': 'Purple-rumped Sunbird',
            'consumer_type': 'bird',
            'resource': 'Lantana',
            'resource_type': 'nectar_source',
            'relationship': 'nectarivory',
            'description': 'Purple-rumped Sunbird feeds on Lantana nectar'
        },
        {
            'consumer': 'Asian Koel',
            'consumer_type': 'bird',
            'resource': 'Banyan',
            'resource_type': 'fruit',
            'relationship': 'frugivory',
            'description': 'Asian Koel feeds on Banyan figs'
        }
    ]
    
    points = []
    
    for idx, rel in enumerate(relationships):
        text = (
            f"{rel['consumer']} ({rel['consumer_type']}) depends on "
            f"{rel['resource']} ({rel['resource_type']}) for {rel['relationship']}: "
            f"{rel['description']}"
        )
        
        vector = embedder.encode(text).tolist()
        
        payload = {
            **rel,
            'text_description': text
        }
        
        point = PointStruct(
            id=idx + 1,
            vector=vector,
            payload=payload
        )
        
        points.append(point)
    
    client.upsert(
        collection_name='species_metadata',
        points=points
    )
    
    print(f"  ✅ Ingested {len(relationships)} species relationships")

def verify_ingestion():
    
    print("\n✅ Verifying ingestion...")
    
    for collection_name in COLLECTIONS.keys():
        info = client.get_collection(collection_name)
        print(f"  📊 {collection_name}: {info.points_count:,} points")

def main():
    
    create_collections()
    
    ingest_observations()
    ingest_climate_data()
    ingest_phenology_patterns()
    ingest_species_metadata()
    
    verify_ingestion()
    
    print("\n" + "="*70)
    print("🎉 QDRANT INGESTION COMPLETE!")
    print("="*70)
    print("\n✅ All data loaded into Qdrant vector database")
    
if __name__ == "__main__":
    main()