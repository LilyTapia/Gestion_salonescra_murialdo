# Export Functionality - PDF and Excel Reports

## Overview
The library management system now supports exporting reports in both PDF and Excel formats. This functionality allows administrators to generate professional reports with all the data from the reports dashboard.

## Features

### PDF Export
- **Professional formatting** with tables, headers, and styling
- **Summary statistics** section with key metrics
- **Room usage breakdown** showing reservation counts per room
- **Material demand analysis** with total quantities requested
- **Automatic filename** with date range (e.g., `reporte_biblioteca_2024-01-01_2024-01-31.pdf`)

### Excel Export
- **Multi-sheet workbook** with organized data:
  - **Resumen**: Summary statistics
  - **Reservas por Salón**: Room reservation data
  - **Materiales Solicitados**: Material usage statistics
- **Professional styling** with colored headers and proper formatting
- **Auto-sized columns** for optimal readability
- **Automatic filename** with date range (e.g., `reporte_biblioteca_2024-01-01_2024-01-31.xlsx`)

## Installation

### Dependencies
Add the following to your `requirements.txt`:
```
reportlab==4.0.7
openpyxl==3.1.2
```

Install the dependencies:
```bash
pip install reportlab==4.0.7 openpyxl==3.1.2
```

## Usage

### Access Requirements
- Only **library administrators** (staff users or AdminBiblioteca group members) can access export functionality
- Export buttons appear in the reports dashboard at `/reportes/`

### How to Export

1. **Navigate to Reports**
   - Go to `/reportes/` in your browser
   - Login as an administrator if not already logged in

2. **Set Filters** (Optional)
   - Select start and end dates for the report period
   - Choose a specific room or leave "All rooms" selected
   - Click "Generar reporte" to update the data

3. **Export Data**
   - Click **📄 Exportar PDF** for PDF format
   - Click **📊 Exportar Excel** for Excel format
   - Files will download automatically with descriptive names

### Export Content

Both formats include:
- **Report period** (date range)
- **Total reservations** count
- **Number of rooms used**
- **Types of materials** requested
- **Detailed room statistics** with reservation counts
- **Material usage statistics** with total quantities

## Technical Implementation

### URL Endpoints
- `/reportes/exportar/pdf/` - PDF export
- `/reportes/exportar/excel/` - Excel export

### Views
- `export_reports_pdf()` - Generates PDF using ReportLab
- `export_reports_excel()` - Creates Excel workbook using OpenPyXL

### Template Integration
Export buttons are integrated into the reports dashboard template with:
- Consistent styling with the existing design
- Responsive layout for mobile devices
- Parameter preservation (filters are maintained in export URLs)

## Testing

Run the test script to verify functionality:
```bash
python3 test_exports.py
```

This will test:
- Library imports
- Basic PDF generation
- Basic Excel generation

## File Structure

```
booking/
├── views.py                 # Export view functions added
├── templates/
│   └── reports/
│       └── dashboard.html   # Export buttons added
└── static/
    └── styles.css          # Export button styling added

salones_cra/
└── urls.py                 # Export URL routes added

requirements.txt            # New dependencies added
test_exports.py            # Test script for export functionality
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure `reportlab` and `openpyxl` are installed
   - Check Python version compatibility

2. **Permission Denied**
   - Verify user has administrator privileges
   - Check `is_library_admin()` function

3. **Empty Reports**
   - Verify there's data in the selected date range
   - Check database connections and models

4. **File Download Issues**
   - Check browser download settings
   - Verify HTTP response headers are correct

### Debug Mode
Enable Django debug mode to see detailed error messages if exports fail.

## Browser Compatibility
- Chrome/Chromium ✅
- Firefox ✅  
- Safari ✅
- Edge ✅

## Performance Notes
- Large date ranges may take longer to process
- PDF generation is typically faster than Excel
- Consider pagination for very large datasets (future enhancement)
