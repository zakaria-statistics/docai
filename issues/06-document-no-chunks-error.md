# Issue: Document Has No Chunks to Add

## What Happened
When adding a PDF:
```
✗ Failed to add document: Document has no chunks to add
```

## Root Cause
The document was processed but produced zero text chunks. Common causes:
1. **Scanned PDF** - Image-based PDF without text layer (needs OCR)
2. **Empty PDF** - File contains no extractable text
3. **Corrupted PDF** - File damaged or improperly formatted
4. **Parsing failure** - PDF loader failed silently

## Diagnosis
Test the PDF manually:
```bash
# Check if PDF has extractable text
docker compose --profile cli run --rm docai bash -c "python3 -c \"
import pypdf
pdf = pypdf.PdfReader('/app/test_docs/Bouvard.pdf')
print(f'Pages: {len(pdf.pages)}')
print(f'First page text: {pdf.pages[0].extract_text()[:200]}')
\""
```

## Resolution Options
1. **If scanned PDF**: Use OCR tool (not currently supported)
2. **If corrupted**: Try re-downloading/converting the PDF
3. **If text exists but not extracted**: Check PDF loader configuration
