# Mastermind Game System SBA report

This directory contains the submission-ready, CLI-centred HKDSE ICT School-based Assessment report:

- [PDF report](Mastermind_Game_System_SBA_Report.pdf) — fixed-layout 41-page A4 submission copy.
- [Word report](Mastermind_Game_System_SBA_Report.docx) — editable copy with linked contents entries.
- [Report source](report_source.md) — inspectable 11,600-word manuscript.
- [Generated figures](assets) — 22 architecture, flow, code, test, and evaluation visuals.

The report identifies the candidate as **CHAN, YU SHING**, candidate number **Student ID s202101127**, of **CCC Ming Kei College**. Signatures and the declaration date remain blank for completion before formal submission.

## Reproducing the report

The build requires Python with `python-docx`, Pillow, and pdfplumber, plus LibreOffice for final rendering. `verification.json` records the measured 25 November 2026 test counts and branch-aware coverage consumed by the figure generator.

```console
python generate_report_assets.py
python build_report.py --output report-pass-1.docx
# Render pass 1 to PDF, then extract physical heading pages.
python extract_page_map.py \
  --source report_source.md \
  --pdf report-pass-1.pdf \
  --output page-map.json
python build_report.py \
  --output Mastermind_Game_System_SBA_Report.docx \
  --page-map page-map.json
```

The committed PDF was rendered from the final DOCX and inspected page by page. The final audits resolved all 96 headings in the contents map, found zero automated document accessibility issues, and confirmed that every table cell survived PDF rendering. The manuscript includes offline and online CLI design, a GUI workflow mapping, real API/WebSocket evidence, a user manual, evaluation, and future improvements.
