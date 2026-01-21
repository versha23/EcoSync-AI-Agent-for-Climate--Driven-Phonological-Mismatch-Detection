"""
 climate data for Karnataka from NASA POWER API
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime

print("🌡️ DOWNLOADING CLIMATE DATA FOR KARNATAKA")
print("="*70)
print("Source: NASA POWER (Prediction of Worldwide Energy Resources)")
print("="*70)

# Karnataka center coordinates
KARNATAKA_CENTER = {
    'latitude': 15.0,   # Center of Karnataka
    'longitude': 76.0
}

# Date range
START_DATE = '20190101'
END_DATE = '20241231'

def download_nasa_power_data():
    
    
    print(f"\n📍 Location: Karnataka, India ({KARNATAKA_CENTER['latitude']}°N, {KARNATAKA_CENTER['longitude']}°E)")
    print(f"📅 Date Range: 2019-2024")
    print(f"🔄 Downloading... (this may take 1-2 minutes)")
    
    # NASA POWER API endpoint
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params = {
        'parameters': 'T2M,T2M_MAX,T2M_MIN,PRECTOTCORR',  # Temperature + Rainfall
        'community': 'AG',  # Agricultural community
        'longitude': KARNATAKA_CENTER['longitude'],
        'latitude': KARNATAKA_CENTER['latitude'],
        'start': START_DATE,
        'end': END_DATE,
        'format': 'JSON'
    }
    
    try:
        response = requests.get(url, params=params, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
        
        data = response.json()
        
        # Extract parameters
        dates = list(data['properties']['parameter']['T2M'].keys())
        temp_mean = list(data['properties']['parameter']['T2M'].values())
        temp_max = list(data['properties']['parameter']['T2M_MAX'].values())
        temp_min = list(data['properties']['parameter']['T2M_MIN'].values())
        rainfall = list(data['properties']['parameter']['PRECTOTCORR'].values())
        
        
        df = pd.DataFrame({
            'date': pd.to_datetime(dates, format='%Y%m%d'),
            'temperature_mean': temp_mean,
            'temperature_max': temp_max,
            'temperature_min': temp_min,
            'rainfall_mm': rainfall
        })
        
        
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_year'] = df['date'].dt.dayofyear
        
        
        baseline_years = [2019, 2020]
        baseline_df = df[df['year'].isin(baseline_years)]
        
        
        baseline_temps = baseline_df.groupby('day_of_year')['temperature_mean'].mean()
        
       
        df['temperature_anomaly'] = df.apply(
            lambda row: row['temperature_mean'] - baseline_temps.get(row['day_of_year'], row['temperature_mean']),
            axis=1
        )
        
         
        df['season'] = df['month'].apply(lambda m: 'pre_monsoon' if m in [3,4,5] else 'other')
        
        
        df.to_csv('data/raw/karnataka_climate_daily.csv', index=False)
        print(f"\n✅ Downloaded {len(df):,} daily records")
        print(f"📁 Saved to: data/raw/karnataka_climate_daily.csv")
        
        
        monthly = df.groupby(['year', 'month']).agg({
            'temperature_mean': 'mean',
            'temperature_max': 'mean',
            'temperature_min': 'mean',
            'rainfall_mm': 'sum',
            'temperature_anomaly': 'mean'
        }).reset_index()
        
        monthly['season'] = monthly['month'].apply(lambda m: 'pre_monsoon' if m in [3,4,5] else 'other')
        
        monthly.to_csv('data/raw/karnataka_climate_monthly.csv', index=False)
        print(f"📁 Saved monthly summary to: data/raw/karnataka_climate_monthly.csv")
        
        
        print(f"\n📊 Climate Data Summary:")
        print(f"   Temperature range: {df['temperature_mean'].min():.1f}°C to {df['temperature_mean'].max():.1f}°C")
        print(f"   Mean temperature: {df['temperature_mean'].mean():.1f}°C")
        print(f"   Total records: {len(df):,} days")
        print(f"   Pre-monsoon records: {len(df[df['season']=='pre_monsoon']):,} days")
        
        
        yearly_temp = df.groupby('year')['temperature_mean'].mean()
        print(f"\n📈 Temperature Trend:")
        for year in sorted(df['year'].unique()):
            year_temp = yearly_temp[year]
            print(f"   {year}: {year_temp:.2f}°C")
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    climate_data = download_nasa_power_data()
    
    if climate_data is not None:
        print("\n" + "="*70)
        print("✅ CLIMATE DATA DOWNLOAD COMPLETE!")
        print("="*70)
        print("\nFiles created:")
        print("  - karnataka_climate_daily.csv   (Daily data)")
        print("  - karnataka_climate_monthly.csv (Monthly summary)")
        
    else:
        print("\n❌ Download failed. See errors above.")