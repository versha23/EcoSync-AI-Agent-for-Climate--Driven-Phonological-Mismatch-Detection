"""
Download phenology observations for all 10 species from iNaturalist

"""
import requests
import pandas as pd
from time import sleep
import os
from datetime import datetime
from tqdm import tqdm


os.makedirs('data/raw', exist_ok=True)

# Karnataka bounding box coordinates
# Southwest: 11.5°N, 74°E
# Northeast: 18.5°N, 78.5°E
KARNATAKA_BOUNDS = {
    'nelat': 18.5,   # North-East latitude
    'nelng': 78.5,   # North-East longitude
    'swlat': 11.5,   # South-West latitude
    'swlng': 74.0    # South-West longitude
}


SPECIES = {
    'papilio_polytes': {
        'taxon_id': 48662, 
        'name': 'Common Mormon',
        'type': 'butterfly'
    },
    'danaus_chrysippus': {
        'taxon_id': 48627, 
        'name': 'Plain Tiger',
        'type': 'butterfly'
    },
    'apis_cerana': {
        'taxon_id': 119826, 
        'name': 'Asian Honey Bee',
        'type': 'bee'
    },
    'apis_dorsata': {
        'taxon_id': 119293, 
        'name': 'Giant Honey Bee',
        'type': 'bee'
    },
    'leptocoma_zeylonica': {
        'taxon_id': 9496, 
        'name': 'Purple-rumped Sunbird',
        'type': 'bird'
    },
    'eudynamys_scolopaceus': {
        'taxon_id': 5253, 
        'name': 'Asian Koel',
        'type': 'bird'
    },
    'murraya_koenigii': {
        'taxon_id': 508988, 
        'name': 'Curry Leaf',
        'type': 'plant'
    },
    'mangifera_indica': {
        'taxon_id': 76625, 
        'name': 'Mango',
        'type': 'plant'
    },
    'ficus_benghalensis': {
        'taxon_id': 54774, 
        'name': 'Banyan',
        'type': 'plant'
    },
    'lantana_camara': {
        'taxon_id': 58791, 
        'name': 'Lantana',
        'type': 'plant'
    }
}

def download_species_observations(species_key, taxon_id, species_name, species_type, max_pages=25):
   
    print(f"\n📥 Downloading {species_name} ({species_type})...")
    
    all_observations = []
    page = 1
    
    pbar = tqdm(total=max_pages, desc=f"  Pages", unit="page")
    
    while page <= max_pages:
        url = "https://api.inaturalist.org/v1/observations"
        
        # API parameters -
        params = {
            'taxon_id': taxon_id,
            'nelat': KARNATAKA_BOUNDS['nelat'],
            'nelng': KARNATAKA_BOUNDS['nelng'],
            'swlat': KARNATAKA_BOUNDS['swlat'],
            'swlng': KARNATAKA_BOUNDS['swlng'],
            'quality_grade': 'research',
            'd1': '2019-01-01',
            'd2': '2024-12-31',
            'per_page': 200,
            'page': page,
            'order': 'desc',
            'order_by': 'created_at'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
           
            if page == 1:
                print(f"  🔍 API Status: {response.status_code}")
            
            if response.status_code == 422:
                print(f"  ⚠️  API parameter error. Trying simpler query...")
                
                params = {
                    'taxon_id': taxon_id,
                    'place_id': 6681,  # India (broader)
                    'quality_grade': 'research',
                    'd1': '2019-01-01',
                    'd2': '2024-12-31',
                    'per_page': 200,
                    'page': page
                }
                response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"  ⚠️  HTTP {response.status_code} on page {page}")
                if page == 1:
                    print(f"  Response: {response.text[:200]}")
                break
            
            data = response.json()
            
            if not data.get('results'):
                if page == 1:
                    print(f"  ⚠️  No results in response")
                break
            
            results = data['results']
            
            
            for obs in results:
                
                lat = None
                lng = None
                if obs.get('geojson'):
                    coords = obs['geojson'].get('coordinates', [])
                    if len(coords) == 2:
                        lng, lat = coords
                
               
                if lat and lng:
                    if not (KARNATAKA_BOUNDS['swlat'] <= lat <= KARNATAKA_BOUNDS['nelat'] and
                           KARNATAKA_BOUNDS['swlng'] <= lng <= KARNATAKA_BOUNDS['nelng']):
                        continue 
                
                record = {
                    'observation_id': obs['id'],
                    'species_scientific': obs['taxon']['name'],
                    'species_common': species_name,
                    'species_type': species_type,
                    'observed_date': obs.get('observed_on'),
                    'latitude': lat,
                    'longitude': lng,
                    'place': obs.get('place_guess', ''),
                    'quality_grade': obs.get('quality_grade'),
                    'user': obs.get('user', {}).get('login', 'unknown'),
                    'photo_count': len(obs.get('photos', [])),
                    'photo_url': obs['photos'][0].get('url') if obs.get('photos') else None
                }
                all_observations.append(record)
            
            pbar.update(1)
            
           
            total_results = data.get('total_results', 0)
            if page * 200 >= total_results:
                break
            
            page += 1
            sleep(1)  # Rate limiting
            
        except requests.exceptions.RequestException as e:
            print(f"\n  ❌ Network error on page {page}: {e}")
            break
        except Exception as e:
            print(f"\n  ❌ Unexpected error on page {page}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    pbar.close()
    
    if all_observations:
        df = pd.DataFrame(all_observations)
        
       
        df = df.drop_duplicates(subset=['observation_id'])
        
        
        df['observed_date'] = pd.to_datetime(df['observed_date'], errors='coerce')
        df = df.dropna(subset=['observed_date'])  # Remove records without dates
        
        df['year'] = df['observed_date'].dt.year
        df['month'] = df['observed_date'].dt.month
        df['day_of_year'] = df['observed_date'].dt.dayofyear
        
       
        filename = f'data/raw/{species_key}.csv'
        df.to_csv(filename, index=False)
        
        print(f"  ✅ Saved {len(df):,} observations to {filename}")
        return df
    else:
        print(f"  ⚠️  No observations found for {species_name}")
        return None


def download_all_species():
    
    print("="*70)
    print("🌍 DOWNLOADING PHENOLOGY DATA FROM INATURALIST")
    print("="*70)
    print(f"📅 Date range: 2019-2024")
    print(f"📍 Region: Karnataka, India (Bounding Box)")
    print(f"🔬 Quality: Research grade only")
    print("="*70)
    
    results = {}
    total_observations = 0
    
    for species_key, info in SPECIES.items():
        df = download_species_observations(
            species_key=species_key,
            taxon_id=info['taxon_id'],
            species_name=info['name'],
            species_type=info['type'],
            max_pages=25
        )
        
        if df is not None:
            results[species_key] = df
            total_observations += len(df)
        
        sleep(2) 
    
    
    print("\n" + "="*70)
    print("✅ DOWNLOAD COMPLETE!")
    print("="*70)
    
    if results:
        print(f"\n📊 Summary by species type:\n")
        
        for species_type in ['plant', 'butterfly', 'bee', 'bird']:
            type_species = {k: v for k, v in results.items() 
                           if SPECIES[k]['type'] == species_type}
            type_count = sum(len(df) for df in type_species.values())
            print(f"  {species_type.capitalize():12} {type_count:,} observations across {len(type_species)} species")
        
        print(f"\n  📈 TOTAL: {total_observations:,} observations")
        print(f"  📁 Saved to: data/raw/")
        
        
        summary = []
        for species_key, df in results.items():
            summary.append({
                'species': SPECIES[species_key]['name'],
                'type': SPECIES[species_key]['type'],
                'observations': len(df),
                'date_range': f"{df['observed_date'].min().date()} to {df['observed_date'].max().date()}",
                'file': f'{species_key}.csv'
            })
        
        summary_df = pd.DataFrame(summary)
        summary_df.to_csv('data/raw/download_summary.csv', index=False)
        print(f"\n  📋 Summary saved to: data/raw/download_summary.csv")
        
    else:
        print("\n⚠️  No data downloaded. Check API connectivity.")
    
    return results


if __name__ == "__main__":
    data = download_all_species()
    
    if data:
        print("\n" + "="*70)
        print("🎉 Ready for next step: Data cleaning and filtering!")
        print("="*70)
    else:
        print("\n" + "="*70)
        print("⚠️  Download failed. Please check errors above.")
        print("="*70)