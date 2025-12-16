import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Material Data Filter", layout="wide")

st.title("Material Data Filter & Merger")
st.markdown("Upload your 4 data files to generate a filtered output file.")

# Create columns for file uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Distribution Chain File")
    st.caption("Expected: Excel file (.xlsx) with columns: Material, St. Create using SQ00 --> Material --> GOVSINCODE --> DCHAIN NII RK (Divisions 31, 32, 36, 37, 38)")
    st.caption("Filter: Only materials where 'St' column is empty")
    dchain_file = st.file_uploader("Upload dchain.xlsx", type=['xlsx'], key='dchain')

    st.subheader("2. Images File")
    st.caption("Expected: CSV file from Eric Flem (NII image database dataset) with columns: Part Number, Images")
    st.caption("Filter: Only parts where 'Images' column is <= 1")
    images_file = st.file_uploader("Upload images.csv", type=['csv'], key='images')

with col2:
    st.subheader("3. Inventory File")
    st.caption("Expected: Excel file (.xlsx) with columns: Material, Type, Description, StorLoc, Available. Create using SQ00 --> ZMM00091 --> Divisions 31, 32, 36, 37, 38 --> Plant 9100, 9300, SLoc (191, 9391")
    st.caption("Filter: Available > 0 AND Type not in ['ZZIW', 'ZZOW']")
    inventory_file = st.file_uploader("Upload Inventory.xlsx", type=['xlsx'], key='inventory')

    st.subheader("4. Revenue File")
    st.caption("Expected: Excel file (.xls) with Sheet1, header at row 39. Use BW --> Revenue Units & Dollars 7x")
    st.caption("Contains: Material and Units columns")
    revenue_file = st.file_uploader("Upload Revenue Units file", type=['xls', 'xlsx'], key='revenue')

# Process button
if st.button("Process Files", type="primary", disabled=not all([dchain_file, images_file, inventory_file, revenue_file])):
    try:
        with st.spinner("Processing files..."):
            # Read all files
            st.info("Reading files...")

            # 1. Read dchain.xlsx - filter where St column is empty
            dchain = pd.read_excel(dchain_file)
            dchain_filtered = dchain[dchain['St'].isna()][['Material']].copy()
            st.success(f"✓ dchain: {len(dchain_filtered)} materials with empty St column")

            # 2. Read images.csv - filter where Images <= 1
            images = pd.read_csv(images_file)
            images['Part Number'] = images['Part Number'].astype(str).str.strip()
            images_filtered = images[images['Images'] <= 1][['Part Number', 'Images']].copy()
            images_filtered.rename(columns={'Part Number': 'Material', 'Images': 'Image #'}, inplace=True)
            st.success(f"✓ images: {len(images_filtered)} parts with Images <= 1")

            # 3. Read Inventory.xlsx - filter where Available > 0 AND Type not in ['ZZIW', 'ZZOW']
            inventory = pd.read_excel(inventory_file)
            inventory_filtered = inventory[
                (inventory['Available'] > 0) &
                (~inventory['Type'].isin(['ZZIW', 'ZZOW']))
            ][['Material', 'Description', 'StorLoc']].copy()
            st.success(f"✓ inventory: {len(inventory_filtered)} items with Available > 0 and Type not ZZIW/ZZOW")

            # 4. Read Revenue file (Sheet1, header at row 38)
            revenue = pd.read_excel(revenue_file, sheet_name='Sheet1', header=38)
            revenue_filtered = revenue[['Material', 'Units']].copy()
            revenue_filtered.rename(columns={'Units': 'units sold'}, inplace=True)
            revenue_filtered['Material'] = revenue_filtered['Material'].astype(str).str.strip()
            st.success(f"✓ revenue: {len(revenue_filtered)} materials with units data")

            # Convert all Material columns to string for consistent merging
            dchain_filtered['Material'] = dchain_filtered['Material'].astype(str).str.strip()
            inventory_filtered['Material'] = inventory_filtered['Material'].astype(str).str.strip()
            images_filtered['Material'] = images_filtered['Material'].astype(str).str.strip()

            st.info("Merging datasets...")

            # Merge the dataframes
            result = inventory_filtered.copy()

            # Filter to only materials that have empty St in dchain
            result = result.merge(dchain_filtered[['Material']], on='Material', how='inner')
            st.success(f"✓ After dchain filter: {len(result)} materials")

            # Add units sold from revenue
            result = result.merge(revenue_filtered, on='Material', how='left')
            st.success(f"✓ After adding revenue: {len(result)} materials")

            # Add Image # from images
            result = result.merge(images_filtered, on='Material', how='left')
            st.success(f"✓ After adding images: {len(result)} materials")

            # Consolidate StorLoc: if a material has both 9191 and 9391, set StorLoc to "BOTH"
            st.info("Consolidating StorLoc values...")

            def consolidate_storloc(group):
                storlocs = group['StorLoc'].unique()
                # Check if material has both 9191 and 9391
                if (9191.0 in storlocs or 9191 in storlocs) and (9391.0 in storlocs or 9391 in storlocs):
                    # Combine into single row with StorLoc = "BOTH"
                    row = group.iloc[0].copy()
                    row['StorLoc'] = 'BOTH'
                    return pd.DataFrame([row])
                else:
                    # Keep all rows as-is
                    return group

            result = result.groupby('Material', group_keys=False).apply(consolidate_storloc).reset_index(drop=True)
            st.success(f"✓ After consolidating StorLoc: {len(result)} materials")

            # Reorder columns as requested
            result = result[['Material', 'Description', 'units sold', 'Image #', 'StorLoc']]

            # Remove any remaining duplicates
            result = result.drop_duplicates(subset=['Material', 'StorLoc'])

            # Store in session state
            st.session_state['result'] = result

            st.success(f"Processing complete! Total records: {len(result)}")

    except Exception as e:
        st.error(f"Error processing files: {str(e)}")
        st.exception(e)

# Display results and download button
if 'result' in st.session_state:
    st.divider()
    st.subheader("Results")

    result = st.session_state['result']

    # Show statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(result))
    with col2:
        st.metric("With Units Sold", result['units sold'].notna().sum())
    with col3:
        st.metric("With Images", result['Image #'].notna().sum())
    with col4:
        storloc_both = (result['StorLoc'] == 'BOTH').sum()
        st.metric("StorLoc = BOTH", storloc_both)

    # Preview data
    st.subheader("Preview (first 20 rows)")
    st.dataframe(result.head(20), use_container_width=True)

    # Download button
    st.subheader("Download Results")

    # Convert to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        result.to_excel(writer, index=False, sheet_name='Filtered Data')
    output.seek(0)

    st.download_button(
        label="Download filtered_output.xlsx",
        data=output,
        file_name="filtered_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )

    # Option to download as CSV as well
    csv = result.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download as CSV",
        data=csv,
        file_name="filtered_output.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.caption("Upload all 4 files and click 'Process Files' to generate your filtered output.")
