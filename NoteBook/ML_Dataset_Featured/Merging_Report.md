# Dataset Merging Report

## 1. Datasets Merged
- Crop_Featured.csv (base dataset)
- Soil_Featured.csv
- Fertilizer_Featured.csv
- Pesticide_Featured.csv
- Rainfall_Featured.csv (aggregated to state level)
- Temperature_Featured.csv (aggregated to state level)

## 2. Merge Keys & Row/Column Impact
| Dataset Merged | Merge Keys | Rows Before | Rows After | Columns Added |
|---|---|---|---|---|
| Soil | District_Name (Crop) -> District (Soil) | 246,091 | 246,091 | +6 |
| Fertilizer | State_Name (Crop) -> State/UT (Fertilizer) | 246,091 | 246,091 | +1 |
| Pesticide | State_Name, Crop_Year (Crop) -> State/UT, Crop_Year (Pesticide) | 246,091 | 246,091 | +1 |
| Rainfall (state-aggregated) | Station -> State (synthetic mapping) -> State_Name (Crop) | 246,091 | 246,091 | +3 |
| Temperature (state-aggregated) | Station -> State (synthetic mapping) -> State_Name (Crop) | 246,091 | 246,091 | +2 |

**Base Crop dataset:** 246,091 rows, 14 columns
**Final merged dataset:** 246,091 rows, 31 columns

All merges used **LEFT JOINs** on the Crop dataset to preserve every original
crop-year-season observation, regardless of whether matching soil, fertilizer,
pesticide, or climate data was available.

## 3. Missing Value Handling (post-merge)
Numeric columns introduced by the merges were filled using **state-level
median**, falling back to the **national median** only when a state had zero
coverage for that column.

| Column | Missing (before) | Filled via State Median | Filled via National Median |
|---|---|---|---|
| pH Level | 242498 | 8921 | 233577 |
| Organic Matter (%) | 242498 | 8921 | 233577 |
| Nitrogen Content (kg/ha) | 242498 | 8921 | 233577 |
| Potassium Content (kg/ha) | 242498 | 8921 | 233577 |
| Soil_Fertility_Index | 242498 | 8921 | 233577 |
| Pesticide_Consumption | 245564 | 13048 | 232516 |
| Annual_Rainfall | 263 | 0 | 263 |
| Average_Rainfall | 263 | 0 | 263 |
| Rainy_Months_Count | 263 | 0 | 263 |
| Average_Temperature | 263 | 0 | 263 |
| Temperature_Range | 263 | 0 | 263 |
| Soil Type | 242498 | 8921 | 233577 |

**Total remaining missing values after treatment:** 0

## 4. Synthetic Station -> State Mapping Explanation
Rainfall and Temperature datasets are recorded at IMD weather-station
granularity and share no direct key with the Crop dataset (State/District).
A `Station_State_Mapping` table (111 stations) was built by
assigning each station to the **real Indian state in which it is physically
located** (e.g. "Bangalore" -> Karnataka, "Srinagar" -> Jammu And Kashmir).
For stations in Union Territories absent from the Crop dataset (Lakshadweep
islands, Delhi), the **nearest geographically adjacent state** was used
(e.g. Delhi stations -> Haryana) so no station's signal was discarded. No
station was ever assigned an arbitrary or random state. Rainfall and
Temperature values themselves were never fabricated — only real recorded
station values were averaged after the mapping.

Rainfall/Temperature were then aggregated to state level as the **mean**
across all stations and months mapped to that state, and merged into the
Crop-based dataset on `State_Name`.

## 5. Feature Engineering Summary
Four new cross-domain features were derived from the merged data:

| Feature | Formula |
|---|---|
| `Weather_Index` | (Average_Temperature × Annual_Rainfall) / 100 |
| `Climate_Index` | Annual_Rainfall / Temperature_Range |
| `Input_Intensity` | Fertilizer_Consumption + Pesticide_Consumption |
| `Agricultural_Intensity` | Input_Intensity × Soil_Fertility_Index |

## 6. Output
Final merged dataset saved to **Final_Crop_Yield_Dataset.csv**
(246,091 rows × 31 columns).
