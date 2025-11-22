# report/data_model.py

def empty_report():
    return {
        "client": "",
        "project": "",
        "tester": "",
        "contact": "",
        "date": "",
        "version": "1.0",
        "executive_summary": "",
        "scope": "",
        "scope_exclusions": "",
        "allowances": "",
        "findings": [],
        "additional_reports": [],
        "vuln_summary": {},
        "watermark_enabled": False,
        "logo_b64": "",
    }
