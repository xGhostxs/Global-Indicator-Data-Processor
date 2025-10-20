"""
Global Indicator Data Processor
===============================
Reads and processes World Development Indicator–style datasets.
Keeps all indicators, countries, and years (no filtering or averaging).
Large data automatically split into multiple Excel sheets.
"""

import pandas as pd
from pathlib import Path

# ============================================================================
# SETTINGS
# ============================================================================

# Input CSV files (rename as needed)
FILE_MAIN = "data_main.csv"          # formerly WDICSV.csv
FILE_COUNTRY = "data_country.csv"    # formerly WDICountry.csv

# Output Excel file
OUTPUT_EXCEL = "global_indicator_output.xlsx"


# ============================================================================
# SAFE CSV READER
# ============================================================================

def safe_read(file_name):
    """Read a CSV file safely using multiple encodings."""
    file_path = Path(file_name)
    if not file_path.exists():
        print(f"\n❌ ERROR: '{file_name}' not found!")
        return None

    encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-9']
    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=enc,
                sep=',',
                low_memory=False,
                na_values=['..', '', ' ', 'NA', 'N/A', '#N/A']
            )
            print(f"✓ '{file_name}' read successfully (encoding: {enc})")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"❌ Read error: {e}")
            return None

    print(f"❌ '{file_name}' could not be read with any encoding!")
    return None


# ============================================================================
# DATA PREPARATION
# ============================================================================

def prepare_data():
    """Read, clean, and reshape the dataset (keep all indicators & years)."""

    print("\n" + "="*70)
    print("GLOBAL INDICATOR DATA PREPARATION")
    print("="*70)

    # Read main data
    df = safe_read(FILE_MAIN)
    if df is None:
        return None, None

    df.columns = df.columns.str.strip()

    # Identify key columns
    country_col = next((c for c in df.columns if 'Country Code' in c), None)
    indicator_col = next((c for c in df.columns if 'Indicator Code' in c), None)
    indicator_name_col = next((c for c in df.columns if 'Indicator Name' in c), None)

    if not country_col or not indicator_col:
        print("❌ Required columns not found!")
        return None, None

    # Detect year columns
    year_cols = [col for col in df.columns if any(x in str(col) for x in ['20', '19', 'YR'])]
    id_cols = [col for col in df.columns if col not in year_cols]

    print(f"   → {len(year_cols)} year columns detected.")

    # Convert to long format
    print("[2/3] Converting to long format...")
    df_long = pd.melt(
        df,
        id_vars=id_cols,
        value_vars=year_cols,
        var_name='Year',
        value_name='Value'
    )

    # Clean year & numeric values
    df_long['Year'] = df_long['Year'].astype(str).str.extract(r'(\d{4})', expand=False)
    df_long = df_long[df_long['Year'].notna()]
    df_long['Year'] = df_long['Year'].astype(int)
    df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
    df_long = df_long.dropna(subset=['Value'])

    print(f"   → {len(df_long):,} clean records ready.")

    # Add country info
    try:
        df_country = safe_read(FILE_COUNTRY)
        if df_country is not None:
            df_country.columns = df_country.columns.str.strip()
            df_country_info = df_country[['Country Code', 'Income Group']].rename(columns={'Country Code': country_col})
            df_long = pd.merge(df_long, df_country_info, on=country_col, how='left')
            print("   → Country info merged.")
    except Exception as e:
        print(f"⚠ Could not merge country info: {e}")

    indicator_info = df[[indicator_col, indicator_name_col]].drop_duplicates() if indicator_name_col else None

    print(f"\n✓ Total {len(df_long):,} country–year–indicator records ready.")
    return df_long, indicator_info


# ============================================================================
# SAVE AND DISPLAY
# ============================================================================

def save_and_show(df, indicator_info, output_excel=OUTPUT_EXCEL):
    """Save the processed data into Excel (splitting large datasets safely)."""
    if df is None:
        return

    print("\n" + "="*70)
    print("EXPORTING TO EXCEL (AUTO-SPLIT MODE)")
    print("="*70)

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)
    print("\n📊 SAMPLE (15 ROWS):")
    print(df.head(15).to_string(index=False))

    EXCEL_MAX_ROWS = 1048576
    SAFE_MAX = EXCEL_MAX_ROWS - 1

    try:
        with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
            indicator_cols = [c for c in df.columns if 'Indicator Code' in c or c.lower() in ('indicator code','indicator_code','indicatorcode')]
            indicator_col = indicator_cols[0] if indicator_cols else None

            if indicator_col is None:
                # Split by row count
                total_rows = len(df)
                for i, start in enumerate(range(0, total_rows, SAFE_MAX), start=1):
                    part_df = df.iloc[start:start+SAFE_MAX]
                    sheet_name = f"Part{i}"[:31]
                    part_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"   → Written: '{sheet_name}' ({len(part_df):,} rows)")
            else:
                unique_codes = df[indicator_col].unique()
                print(f"   → {len(unique_codes)} indicators found. Writing by indicator...")
                for code in unique_codes:
                    sub = df[df[indicator_col] == code]
                    n = len(sub)
                    if n == 0:
                        continue

                    if n <= SAFE_MAX:
                        safe_name = str(code)[:28]
                        sub.to_excel(writer, sheet_name=safe_name, index=False)
                        print(f"   → '{safe_name}' ({n:,} rows)")
                    else:
                        parts = (n // SAFE_MAX) + 1
                        for i, start in enumerate(range(0, n, SAFE_MAX), start=1):
                            part_df = sub.iloc[start:start+SAFE_MAX]
                            sheet_name = f"{str(code)[:20]}_p{i}"[:31]
                            part_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            print(f"      → '{sheet_name}' ({len(part_df):,} rows)")

            if indicator_info is not None:
                indicator_info.to_excel(writer, sheet_name='Indicator_Info', index=False)

        print(f"\n✅ Export completed: {output_excel}")
    except PermissionError:
        print("\n❌ Excel file is open! Please close it and retry.")
    except Exception as e:
        print(f"\n❌ Export error: {e}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("GLOBAL INDICATOR DATA READER & EXPORTER")
    print("="*70)

    data, indicator_info = prepare_data()
    save_and_show(data, indicator_info)

    print("\n" + "="*70)
    print("PROCESS COMPLETED SUCCESSFULLY")
    print("="*70 + "\n")
