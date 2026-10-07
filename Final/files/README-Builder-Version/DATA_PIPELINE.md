# Data Pipeline

## Original Datasets

Five Government of India datasets, merged into one final training table
(`Final_Crop_Yield_Dataset.csv`, 246,091 rows):
1. District-wise, season-wise crop production statistics (Crop, Area,
   Production, Yield — the core dataset and target source)
2. Monthly mean max/min temperature and rainfall by station
3. Soil analysis data (pH, Organic Matter, N/P/K by district)
4. State-wise fertilizer consumption
5. State/district-wise pesticide consumption

## Merging Process

All four supplementary datasets are joined onto the crop production table
by state/district (climate and soil data) or state (fertilizer/pesticide
data), matched via normalized name-matching to handle spelling
inconsistencies between government sources (e.g. state name casing/
formatting differences).

## Cleaning Process

**Two categories of cleaning were applied, each with a documented,
data-driven rule — never "remove rows the model gets wrong":**

1. **Sentinel value removal**: `Production == 729.0` exactly — appears
   3,766 times (1.53% of rows) across 58 unrelated crops and 28 states,
   a repeated value that cannot be genuine data, treated as a
   placeholder/default value in the source government data.
2. **Per-crop statistical outlier removal**: `Yield > Q3 + 3×IQR`,
   computed **within each crop's own distribution** (the standard "far
   outlier" Tukey fence, applied per-crop rather than globally because
   different crops use different production units in this dataset — a
   global cutoff would have wrongly discarded Coconut's legitimately high
   nuts/ha values).

Combined: 5,634 rows removed (2.289% of 246,091) — a small, defensible,
fully-documented fraction, not a large or opaque filter.

## Feature Engineering

23 final model features:

| Feature | Derivation |
|---|---|
| `Crop_Year`, `Area` | Raw |
| `Season_Encoded`, `Crop_Encoded`, `State_Name_Encoded`, `District_Name_Encoded` | Label-encoded from the real training data's category↔code pairs |
| `pH Level`, `Organic Matter (%)`, `Nitrogen Content (kg/ha)`, `Potassium Content (kg/ha)` | Raw soil analysis values |
| `Soil_Fertility_Index` | `mean(Nitrogen, Potassium)` — Phosphorus was dropped upstream due to a data-quality issue in the source soil dataset |
| `Soil_Type_Encoded` | `LabelEncoder` fit on the soil type categories |
| `Fertilizer_Consumption`, `Pesticide_Consumption` | Raw, state-level |
| `Annual_Rainfall`, `Average_Rainfall`, `Rainy_Months_Count` | Aggregated from station-level monthly data |
| `Average_Temperature`, `Temperature_Range` | Aggregated from station-level monthly data |
| `Weather_Index` | `(Average_Temperature × Annual_Rainfall) / 100` |
| `Climate_Index` | `Annual_Rainfall / Temperature_Range` |
| `Input_Intensity` | `Fertilizer_Consumption + Pesticide_Consumption` |
| `Agricultural_Intensity` | `Input_Intensity × Soil_Fertility_Index` |

## Encoding

Categorical features (`Crop`, `Season`, `State_Name`, `District_Name`,
`Soil Type`) are integer-encoded via lookup dictionaries built directly
from paired raw/encoded columns already present in the training data
(read, not re-fit blind) — guaranteeing the exact same encoding the
deployed model was trained on. These lookups are shipped as small JSON
files in `backend/artifacts/` so the backend never needs the full raw
dataset at runtime.

## Missing Value Handling

Rows with missing values in any of the 23 features or the target are
dropped before training (`dropna(subset=FEATURES + [TARGET])`) — a
straightforward, defensible approach given the dataset's overall low
missingness after the upstream government-data cleaning stage (see the
Phase 1 dataset report for full missing-value statistics per source file).

## Data Quality Checks

- Per-crop min/median/max yield sanity-checked against real-world
  agronomic ranges to identify the sentinel-value and Punjab-Sugarcane-2011
  anomalies described above.
- Record counts per state checked before using them as an EDA aggregate
  (raw `Production` sums were found to be meaningless across crops with
  mixed units — see `EdaView`'s "Data Coverage" chart, which uses record
  count instead of a production/area volume for exactly this reason).

## Complete Data Flow

```
5 Government CSVs
      │
      ▼
Merge (state/district-matched)
      │
      ▼
Final_Crop_Yield_Dataset.csv (246,091 rows)
      │
      ▼
Drop rows with missing required features/target
      │
      ▼
Remove sentinel (Production==729) + per-crop Tukey far-outlier rows (2.289%)
      │
      ▼
Cleaned, model-ready dataset (240,457 rows)
      │
      ▼
Split per crop (≥500 rows) → 52 crop-specific train/test sets
Remaining smaller crops → 1 pooled train/test set
      │
      ▼
53 trained CatBoost models + encoders + reference statistics → backend/artifacts/
```
