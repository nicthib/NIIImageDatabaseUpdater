# Material Data Filter & Merger

A Streamlit web application for filtering and merging material data from multiple sources.

## Features

- Upload 4 data files through a user-friendly interface
- Automatic data filtering and merging based on business rules
- StorLoc consolidation (combines 9191 and 9391 into "BOTH")
- Download results as Excel or CSV
- Preview results before downloading

## Required Files

1. **Distribution Chain File (dchain.xlsx)**
   - Excel file with Material and St columns
   - Filters materials where St is empty

2. **Images File (images.csv)**
   - CSV file with Part Number and Images columns
   - Filters parts where Images <= 1

3. **Inventory File (Inventory.xlsx)**
   - Excel file with Material, Type, Description, StorLoc, Available columns
   - Filters where Available > 0 AND Type not in ['ZZIW', 'ZZOW']

4. **Revenue File (Revenue Units & Dollars 7x.xls)**
   - Excel file with Sheet1, header at row 39
   - Contains Material and Units columns

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the App

1. Open a terminal/command prompt
2. Navigate to this directory
3. Run:
```bash
streamlit run app.py
```

4. Your browser will automatically open to the app (usually at http://localhost:8501)

## Output

The app generates a file with the following columns:
- **Material** - Product number
- **Description** - Product description
- **units sold** - Units sold from revenue data
- **Image #** - Number of images (0 or 1)
- **StorLoc** - Storage location (9191, 9391, or BOTH)

## Usage

1. Upload all 4 required files
2. Click "Process Files"
3. Review the preview and statistics
4. Click "Download filtered_output.xlsx" to save the results
