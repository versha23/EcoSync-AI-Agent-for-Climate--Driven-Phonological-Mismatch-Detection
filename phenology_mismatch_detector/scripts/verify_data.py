"""
verification of downloaded data
"""
import pandas as pd
import os

print("🔍 VERIFYING DOWNLOADED DATA")
print("="*70)


SPECIES_FILES = [
    'papilio_polytes.csv',
    'danaus_chrysippus.csv',
    'apis_cerana.csv',
    'apis_dorsata.csv',
    'leptocoma_zeylonica.csv',
    'eudynamys_scolopaceus.csv',
    'murraya_koenigii.csv',
    'mangifera_indica.csv',
    'ficus_benghalensis.csv',
    'lantana_camara.csv'
]

total_obs = 0
summary = []

print("\n📋 SPECIES OBSERVATIONS:\n")

for filename in SPECIES_FILES:
    filepath = f'data/raw/{filename}'
    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        count = len(df)
        total_obs += count
        
        species_name = filename.replace('.csv', '').replace('_', ' ').title()
        print(f"  ✅ {species_name:30} {count:>6,} observations")
        
        summary.append({
            'file': filename,
            'observations': count,
            'has_coords': df['latitude'].notna().sum() if 'latitude' in df.columns else 0,
            'has_dates': df['observed_on'].notna().sum() if 'observed_on' in df.columns else 0
        })
    else:
        print(f"  ❌ {filename:30} NOT FOUND")

print(f"\n  {'TOTAL':30} {total_obs:>6,} observations")

# Climate data
print(f"\n🌡️ CLIMATE DATA:\n")

climate_files = [
    ('karnataka_climate_daily.csv', 'Daily'),
    ('karnataka_climate_monthly.csv', 'Monthly')
]

for filename, label in climate_files:
    filepath = f'data/raw/{filename}'
    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        print(f"  ✅ {label:10} {len(df):>6,} records")
    else:
        print(f"  ❌ {label:10} NOT FOUND")

print("\n" + "="*70)
print("✅ DATA VERIFICATION COMPLETE!")
print("="*70)

# Save summary
summary_df = pd.DataFrame(summary)
print(f"\n📊 Data Quality Check:")
print(f"  Files with coordinates: {(summary_df['has_coords'] > 0).sum()}/10")
print(f"  Files with dates: {(summary_df['has_dates'] > 0).sum()}/10")
print(f"  Total observations: {total_obs:,}")

if total_obs >= 3000:
    print(f"\n🎉 EXCELLENT! You have {total_obs:,} observations - more than enough!")
elif total_obs >= 1000:
    print(f"\n✅ GOOD! You have {total_obs:,} observations - sufficient for analysis!")
else:
    print(f"\n⚠️  Only {total_obs:,} observations - might need more data")

