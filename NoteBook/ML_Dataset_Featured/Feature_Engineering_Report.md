# Feature Engineering Report
| Dataset | Features Before | Features After | New Features Added / Operations |
|---------|-----------------|----------------|---------------------------------|
| Crop | 7 | 14 | Yield, Log_Production, Farm_Size, Season_Encoded, Crop_Encoded, State_Name_Encoded, District_Name_Encoded |
| Rainfall | 5 | 8 | Annual_Rainfall, Average_Rainfall, Rainy_Months_Count |
| Temperature | 6 | 8 | Average_Temperature, Temperature_Range |
| Soil | 7 | 7 | Soil_Fertility_Index |
| Fertilizer | 4 | 4 | None |
| Pesticide | 7 | 3 | Year, Pesticide_Consumption (Melted) |

### Additional Transformations
- Safely calculated `Yield` preventing ZeroDivision exceptions.
- Added LabelEncoders for all high-cardinality categorical variables while retaining originals.
- Computed `Soil_Fertility_Index` dynamically based on available N-P-K constraints.
- Cleaned non-numeric anomalies in Pesticide metrics prior to melt operations.
