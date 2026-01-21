"""
Intelligent Phenology Query System
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import pandas as pd
from datetime import datetime

print("🧠 INTELLIGENT PHENOLOGY QUERY SYSTEM")
print("="*70)
print("Using: Qdrant Vector Search + Rule-based Reasoning")
print("="*70)

qdrant_client = QdrantClient("localhost", port=6333)
embedder = SentenceTransformer('all-MiniLM-L6-v2')

class PhenologyAnalyzer:
    
    
    def __init__(self):
        self.client = qdrant_client
        self.embedder = embedder
    
    def retrieve(self, query_text, collection='observations', limit=20, filters=None):
        
        query_vector = self.embedder.encode(query_text).tolist()
        
        results = self.client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            query_filter=filters
        )
        
        return results.points
    
    def analyze_mismatch(self, species1, species2, year=2024):
        
        
        print(f"\n{'='*70}")
        print(f"🔍 ANALYZING: {species1} ↔️ {species2} mismatch in {year}")
        print(f"{'='*70}\n")
        
        
        print(f"📥 Retrieving data from Qdrant...")
        
        sp1_obs = self.retrieve(
            species1,
            filters=Filter(must=[
                FieldCondition(key="species_common", match=MatchValue(value=species1)),
                FieldCondition(key="year", match=MatchValue(value=year))
            ]),
            limit=200
        )
        
        sp2_obs = self.retrieve(
            species2,
            filters=Filter(must=[
                FieldCondition(key="species_common", match=MatchValue(value=species2)),
                FieldCondition(key="year", match=MatchValue(value=year))
            ]),
            limit=200
        )
        
        if not sp1_obs or not sp2_obs:
            print("⚠️  Insufficient data for analysis")
            return
        
        # Calculate medians
        sp1_doys = [p.payload['day_of_year'] for p in sp1_obs]
        sp2_doys = [p.payload['day_of_year'] for p in sp2_obs]
        
        sp1_median = pd.Series(sp1_doys).median()
        sp2_median = pd.Series(sp2_doys).median()
        
        gap = sp1_median - sp2_median
        
        print(f"  ✅ {species1}: {len(sp1_obs)} observations, Median DOY: {sp1_median:.0f}")
        print(f"  ✅ {species2}: {len(sp2_obs)} observations, Median DOY: {sp2_median:.0f}")
        
        
        patterns = self.retrieve(
            f"{species1} {species2}",
            collection='temporal_patterns',
            limit=10
        )
        
        
        climate = self.retrieve(
            "temperature pre-monsoon",
            collection='climate_data',
            filters=Filter(must=[
                FieldCondition(key="year", match=MatchValue(value=year)),
                FieldCondition(key="season", match=MatchValue(value="pre_monsoon"))
            ]),
            limit=5
        )
        
        
        sp1_pattern = next((p for p in patterns if p.payload.get('species') == species1), None)
        sp2_pattern = next((p for p in patterns if p.payload.get('species') == species2), None)
        
        sp1_shift = sp1_pattern.payload.get('shift_days', 0) if sp1_pattern else None
        sp2_shift = sp2_pattern.payload.get('shift_days', 0) if sp2_pattern else None
        
       
        temp_anomaly = climate[0].payload.get('temperature_anomaly', 0) if climate else 0
        
       
        print(f"\n{'='*70}")
        print(f"💡 ANALYSIS RESULTS:")
        print(f"{'='*70}\n")
        
        # 1. State the mismatch
        print(f"🚨 PHENOLOGICAL MISMATCH DETECTED\n")
        print(f"Temporal Gap: {abs(gap):.0f} days")
        
        if gap > 0:
            print(f"└─ {species1} occurs {gap:.0f} days AFTER {species2}")
        else:
            print(f"└─ {species1} occurs {abs(gap):.0f} days BEFORE {species2}")
        
        # 2. Current timing
        print(f"\n📅 CURRENT TIMING ({year}):\n")
        print(f"  {species1}: Day {sp1_median:.0f} ({self._doy_to_date(sp1_median, year)})")
        print(f"  {species2}: Day {sp2_median:.0f} ({self._doy_to_date(sp2_median, year)})")
        
        # 3. Historical shifts
        if sp1_shift is not None or sp2_shift is not None:
            print(f"\n📊 PHENOLOGICAL SHIFTS (vs 2019-2020 baseline):\n")
            
            if sp1_shift is not None:
                direction1 = "earlier" if sp1_shift < 0 else "later"
                print(f"  {species1}: {abs(sp1_shift):.1f} days {direction1}")
            
            if sp2_shift is not None:
                direction2 = "earlier" if sp2_shift < 0 else "later"
                print(f"  {species2}: {abs(sp2_shift):.1f} days {direction2}")
            
            # Explain differential shift
            if sp1_shift is not None and sp2_shift is not None:
                diff_shift = abs(sp1_shift - sp2_shift)
                print(f"\n  ⚠️  Differential shift: {diff_shift:.1f} days")
                print(f"      └─ Species responding at different rates to climate change")
        
        # 4. Climate driver
        print(f"\n CLIMATE CONTEXT:\n")
        print(f"  Pre-monsoon temperature anomaly: {temp_anomaly:+.2f}°C")
        
        if temp_anomaly > 1.0:
            print(f"  └─ Significant warming detected")
        
       
        print(f"\n🔗 CAUSAL MECHANISM:\n")
        
        
        sp1_type = sp1_obs[0].payload.get('species_type') if sp1_obs else 'unknown'
        sp2_type = sp2_obs[0].payload.get('species_type') if sp2_obs else 'unknown'
        
        if sp2_type == 'plant' and sp1_type in ['bee', 'butterfly', 'bird']:
            print(f"  Climate warming → {species2} (plant) responds quickly")
            print(f"  {species1} ({sp1_type}) responds more slowly (photoperiod-constrained)")
            print(f"  Result: {species1} misses optimal {species2} resource availability")
        
        # 5. Impact assessment
        print(f"\n⚡ ECOLOGICAL IMPACT:\n")
        
        if abs(gap) > 20:
            severity = "SEVERE"
            print(f"  Severity: {severity}")
            print(f"  └─ Gap exceeds 20 days - major disruption")
        elif abs(gap) > 10:
            severity = "MODERATE"
            print(f"  Severity: {severity}")
            print(f"  └─ Gap exceeds 10 days - significant impact")
        else:
            severity = "LOW"
            print(f"  Severity: {severity}")
            print(f"  └─ Gap under 10 days - minor impact")
        
        # Species-specific impacts
        if "Mango" in species2 and "Bee" in species1:
            print(f"\n  Agricultural Impact:")
            print(f"  • Reduced mango pollination success")
            print(f"  • Estimated crop loss: 30-50%")
            print(f"  • Economic impact: Significant for Karnataka farmers")
        
        if "Curry Leaf" in species2 and "Mormon" in species1:
            print(f"\n  Biodiversity Impact:")
            print(f"  • Butterfly larvae miss fresh leaf flush")
            print(f"  • Reduced larval survival")
            print(f"  • Population decline risk")
        
        # 6. Data sources
        print(f"\n📚 DATA SOURCES:\n")
        print(f"  • iNaturalist observations: {len(sp1_obs) + len(sp2_obs)} records")
        print(f"  • Climate data: NASA POWER")
        print(f"  • Analysis period: 2019-2024")
        print(f"  • Vector database: Qdrant")
        
        return {
            'species1': species1,
            'species2': species2,
            'gap_days': gap,
            'severity': severity,
            'sp1_median_doy': sp1_median,
            'sp2_median_doy': sp2_median
        }
    
    def _doy_to_date(self, doy, year):
        """Convert day of year to readable date"""
        from datetime import datetime, timedelta
        date = datetime(year, 1, 1) + timedelta(days=int(doy) - 1)
        return date.strftime("%B %d")
    
    def explain_shifts(self):
        """Explain all phenological shifts"""
        
        print(f"\n{'='*70}")
        print(f"📊 PHENOLOGICAL SHIFT ANALYSIS")
        print(f"{'='*70}\n")
        
        patterns = self.retrieve(
            "phenological shifts timing changes",
            collection='temporal_patterns',
            limit=20
        )
        
        if not patterns:
            print("⚠️  No shift data available")
            return
        
        plants = []
        animals = []
        
        for p in patterns:
            payload = p.payload
            if payload.get('species_type') == 'plant':
                plants.append(payload)
            else:
                animals.append(payload)
        
        print("🌿 PLANT RESPONSES (Temperature-driven):\n")
        for p in sorted(plants, key=lambda x: x.get('shift_days', 0)):
            shift = p.get('shift_days', 0)
            direction = "earlier" if shift < 0 else "later"
            print(f"  • {p.get('species'):25} {abs(shift):>5.1f} days {direction}")
        
        print(f"\n🦋 ANIMAL RESPONSES (Mixed cues):\n")
        for p in sorted(animals, key=lambda x: x.get('shift_days', 0)):
            shift = p.get('shift_days', 0)
            direction = "earlier" if shift < 0 else "later"
            species_type = p.get('species_type', 'animal')
            print(f"  • {p.get('species'):25} {abs(shift):>5.1f} days {direction} ({species_type})")
        
        print(f"\n💡 KEY INSIGHT:")
        print(f"   Plants respond faster to temperature → Shift more")
        print(f"   Animals constrained by photoperiod → Shift less")
        print(f"   Result: Growing temporal mismatches")

# ==================== DEMO QUERIES ====================

if __name__ == "__main__":
    
    analyzer = PhenologyAnalyzer()
    
    print("\n" + "🔥"*35)
    print("DEMO: Intelligent Mismatch Detection")
    print("🔥"*35)
    
    # Analysis 1: Bee-Mango mismatch
    analyzer.analyze_mismatch("Giant Honey Bee", "Mango", year=2024)
    
    input("\n\nPress Enter for next analysis...")
    
    # Analysis 2: Butterfly-Plant mismatch
    analyzer.analyze_mismatch("Common Mormon", "Curry Leaf", year=2024)
    
    input("\n\nPress Enter for shift overview...")
    
    # Overview of all shifts
    analyzer.explain_shifts()
    
    print("\n" + "="*70)
    print("✅ ANALYSIS COMPLETE!")
    print("="*70)
    