import pandas as pd
import numpy as np
import os
from datetime import datetime

print("CLEANING AND FILTERING PHENOLOGY DATA")
print("="*70)


os.makedirs('data/processed', exist_ok=True)

KARNATAKA_BOUNDS = {
    'lat_min': 11.5,
    'lat_max': 18.5,
    'lng_min': 74.0,
    'lng_max': 78.5
}


SPECIES_INFO = {
    'papilio_polytes': {'type': 'butterfly', 'common': 'Common Mormon', 'role': 'consumer'},
    'danaus_chrysippus': {'type': 'butterfly', 'common': 'Plain Tiger', 'role': 'consumer'},
    'apis_cerana': {'type': 'bee', 'common': 'Asian Honey Bee', 'role': 'pollinator'},
    'apis_dorsata': {'type': 'bee', 'common': 'Giant Honey Bee', 'role': 'pollinator'},
    'leptocoma_zeylonica': {'type': 'bird', 'common': 'Purple-rumped Sunbird', 'role': 'consumer'},
    'eudynamys_scolopaceus': {'type': 'bird', 'common': 'Asian Koel', 'role': 'consumer'},
    'murraya_koenigii': {'type': 'plant', 'common': 'Curry Leaf', 'role': 'resource'},
    'mangifera_indica': {'type': 'plant', 'common': 'Mango', 'role': 'resource'},
    'ficus_benghalensis': {'type': 'plant', 'common': 'Banyan', 'role': 'resource'},
    'lantana_camara': {'type': 'plant', 'common': 'Lantana', 'role': 'resource'}
}

def clean_species_data(filename, species_key):
    
    
    filepath = f'data/raw/{filename}'
    info = SPECIES_INFO[species_key]
    
    print(f"\n🔧 Processing {info['common']} ({info['type']})...")
    
    
    df = pd.read_csv(filepath)
    original_count = len(df)
    
    
    column_mapping = {
        'id': 'observation_id',
        'observed_on': 'observed_date',
    }
    df = df.rename(columns=column_mapping)
    
    
    required_cols = ['observation_id', 'observed_date', 'latitude', 'longitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"  ⚠️  Missing columns: {missing_cols}")
        
        if 'observed_on' in df.columns and 'observed_date' not in df.columns:
            df['observed_date'] = df['observed_on']
    
    
    df = df.dropna(subset=['observed_date'])
    
    
    df['observed_date'] = pd.to_datetime(df['observed_date'], errors='coerce')
    df = df.dropna(subset=['observed_date'])
      
    df = df[(df['observed_date'] >= '2019-01-01') & (df['observed_date'] <= '2024-12-31')]
      
    df = df.dropna(subset=['latitude', 'longitude'])
    
    df = df[
        (df['latitude'] >= KARNATAKA_BOUNDS['lat_min']) &
        (df['latitude'] <= KARNATAKA_BOUNDS['lat_max']) &
        (df['longitude'] >= KARNATAKA_BOUNDS['lng_min']) &
        (df['longitude'] <= KARNATAKA_BOUNDS['lng_max'])
    ]
    
    df = df.drop_duplicates(subset=['observation_id'])
    
   
    df['year'] = df['observed_date'].dt.year
    df['month'] = df['observed_date'].dt.month
    df['day'] = df['observed_date'].dt.day
    df['day_of_year'] = df['observed_date'].dt.dayofyear
    
   
    def get_season(month):
        if month in [3, 4, 5]:
            return 'pre_monsoon'
        elif month in [6, 7, 8, 9]:
            return 'monsoon'
        elif month in [10, 11]:
            return 'post_monsoon'
        else:
            return 'winter'
    
    df['season'] = df['month'].apply(get_season)
    
   
    df['species_key'] = species_key
    df['species_common'] = info['common']
    df['species_type'] = info['type']
    df['species_role'] = info['role']
    
    
    final_columns = [
        'observation_id', 'species_key', 'species_common', 'species_type', 'species_role',
        'observed_date', 'year', 'month', 'day', 'day_of_year', 'season',
        'latitude', 'longitude', 'place_guess', 'scientific_name', 'quality_grade'
    ]
    
    
    final_columns = [col for col in final_columns if col in df.columns]
    df = df[final_columns]
    
    
    output_file = f'data/processed/{species_key}_cleaned.csv'
    df.to_csv(output_file, index=False)
    
  
    removed = original_count - len(df)
    removal_pct = (removed / original_count * 100) if original_count > 0 else 0
    
    print(f"  📊 Original: {original_count:,} → Cleaned: {len(df):,} (removed {removed:,} / {removal_pct:.1f}%)")
    
    
    year_counts = df['year'].value_counts().sort_index()
    print(f"  📅 Year distribution:")
    for year, count in year_counts.items():
        print(f"     {year}: {count:>4} obs")
    
    return df

def create_combined_dataset(all_data):
    """Combine all species into single dataset"""
    
    print("\n Creating combined dataset...")
    
    combined = pd.concat(all_data.values(), ignore_index=True)
    
    # Save
    combined.to_csv('data/processed/all_species_combined.csv', index=False)
    
    print(f"   Combined dataset: {len(combined):,} observations")
    print(f"   Saved to: data/processed/all_species_combined.csv")
    
    return combined

def create_baseline_vs_current(combined_df):
    """Create baseline (2019-2020) vs current (2022-2024) comparison"""
    
    print("\n📊 Creating baseline vs current datasets...")
    
    baseline = combined_df[combined_df['year'].isin([2019, 2020])]
    current = combined_df[combined_df['year'].isin([2022, 2023, 2024])]
    
    baseline.to_csv('data/processed/baseline_2019_2020.csv', index=False)
    current.to_csv('data/processed/current_2022_2024.csv', index=False)
    
    print(f"  📅 Baseline (2019-2020): {len(baseline):,} observations")
    print(f"  📅 Current (2022-2024): {len(current):,} observations")
    
    return baseline, current

def analyze_temporal_patterns(combined_df):
    
    
    print("\n🔍 Analyzing temporal patterns...")
    
    summary = []
    
    for species_key in SPECIES_INFO.keys():
        species_df = combined_df[combined_df['species_key'] == species_key]
        
        if len(species_df) < 10:
            continue
        
        
        baseline_doy = species_df[species_df['year'].isin([2019, 2020])]['day_of_year'].median()
        current_doy = species_df[species_df['year'].isin([2022, 2023, 2024])]['day_of_year'].median()
        
        shift = current_doy - baseline_doy if (pd.notna(baseline_doy) and pd.notna(current_doy)) else None
        
        summary.append({
            'species': SPECIES_INFO[species_key]['common'],
            'type': SPECIES_INFO[species_key]['type'],
            'total_obs': len(species_df),
            'baseline_median_doy': baseline_doy,
            'current_median_doy': current_doy,
            'shift_days': shift
        })
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv('data/processed/phenology_summary.csv', index=False)
    
    print("\n  📋 Phenological Shift Summary:")
    print(summary_df.to_string(index=False))
    
    return summary_df

def main():
    """Main cleaning pipeline"""
    
    all_data = {}
    
    # Clean each species
    for species_key in SPECIES_INFO.keys():
        filename = f'{species_key}.csv'
        
        if os.path.exists(f'data/raw/{filename}'):
            df = clean_species_data(filename, species_key)
            all_data[species_key] = df
        else:
            print(f"\n  ⚠️  {filename} not found, skipping...")
    
   
    combined = create_combined_dataset(all_data)
    
   
    baseline, current = create_baseline_vs_current(combined)
    
    
    summary = analyze_temporal_patterns(combined)
    
   
    print("\n" + "="*70)
    print("DATA CLEANING COMPLETE!")
    print("="*70)
    
    print(f"\n  Processed files created:")
    print(f"  - Individual species: data/processed/[species]_cleaned.csv (10 files)")
    print(f"  - Combined dataset: data/processed/all_species_combined.csv")
    print(f"  - Baseline period: data/processed/baseline_2019_2020.csv")
    print(f"  - Current period: data/processed/current_2022_2024.csv")
    print(f"  - Summary: data/processed/phenology_summary.csv")
    
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total observations: {len(combined):,}")
    print(f"  Date range: {combined['observed_date'].min().date()} to {combined['observed_date'].max().date()}")
    print(f"  Species with data: {combined['species_key'].nunique()}/10")
    
    by_type = combined.groupby('species_type').size()
    print(f"\n  By type:")
    for stype, count in by_type.items():
        print(f"    {stype.capitalize():12} {count:>5,} observations")
    


if __name__ == "__main__":
    main()