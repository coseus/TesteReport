# ui/findings_tab.py
import streamlit as st
import base64
from util.helpers import resize_image_b64
from report.parsers import auto_parse_findings
from report.numbering import renumber_findings, next_finding_id


SEVERITY_COLORS = {
    "Critical": "#e74c3c",
    "High": "#e67e22",
    "Moderate": "#f1c40f",
    "Low": "#3498db",
    "Informational": "#95a5a6",
}


# ============================================================
# FINDING EDITOR (NO DUPLICATES + NO INVALID IMAGES)
# ============================================================
def _edit_finding_modal(finding: dict, idx: int) -> bool:
    import base64
    from util.helpers import resize_image_b64

    st.subheader(f"Editing Finding #{finding.get('id')}")

    # ---------- CLEAN INVALID IMAGES ----------
    clean_images = []
    for img in finding.get("images", []):
        if not img:
            continue
        if not isinstance(img, str):
            continue
        if len(img.strip()) % 4 != 0:
            continue
        clean_images.append(img)

    finding["images"] = clean_images
    existing_images = finding["images"]

    # ---------- FIELDS (with unique keys) ----------
    finding["title"] = st.text_input(
        "Title", finding.get("title", ""), key=f"edit_title_{idx}"
    )

    finding["severity"] = st.selectbox(
        "Severity",
        ["Critical", "High", "Moderate", "Low", "Informational"],
        index=["Critical", "High", "Moderate", "Low", "Informational"].index(
            finding.get("severity", "Informational")
        ),
        key=f"edit_severity_{idx}",
    )

    finding["host"] = st.text_input(
        "Host", finding.get("host", ""), key=f"edit_host_{idx}"
    )
    finding["port"] = st.text_input(
        "Port", finding.get("port", ""), key=f"edit_port_{idx}"
    )
    finding["protocol"] = st.text_input(
        "Protocol", finding.get("protocol", ""), key=f"edit_protocol_{idx}"
    )

    finding["cvss"] = st.text_input(
        "CVSS", finding.get("cvss", ""), key=f"edit_cvss_{idx}"
    )
    finding["cve"] = st.text_input(
        "CVE", finding.get("cve", ""), key=f"edit_cve_{idx}"
    )

    finding["description"] = st.text_area(
        "Description", finding.get("description", ""), height=120, key=f"edit_desc_{idx}"
    )
    finding["impact"] = st.text_area(
        "Impact", finding.get("impact", ""), height=120, key=f"edit_imp_{idx}"
    )
    finding["recommendation"] = st.text_area(
        "Recommendation", finding.get("recommendation", ""), height=120, key=f"edit_rec_{idx}"
    )
    finding["code"] = st.text_area(
        "Code / Output", finding.get("code", ""), height=200, key=f"edit_code_{idx}"
    )

    st.markdown("### Existing Evidence Images")

    # ---------- DISPLAY EXISTING IMAGES ----------
    cols = st.columns(4)
    for i, img_b64 in enumerate(existing_images):
        with cols[i % 4]:
            try:
                st.image(img_b64, use_column_width=True)
            except:
                st.warning("⚠️ Invalid image skipped")
                continue

            if st.button(f"Delete {i+1}", key=f"del_img_{idx}_{i}"):
                existing_images.pop(i)
                finding["images"] = existing_images
                st.rerun()

    st.markdown("---")
    st.markdown("### Upload New Evidence Images")

    new_imgs = st.file_uploader(
        "Add more images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key=f"new_upload_{idx}",
    )

    # ---------- SAVE ----------
    if st.button("Save Finding", key=f"save_find_{idx}"):
        if new_imgs:
            for file in new_imgs:
                b64 = base64.b64encode(file.read()).decode("utf-8")
                b64 = resize_image_b64(b64)
                if b64 not in existing_images:
                    existing_images.append(b64)

        finding["images"] = existing_images
        return True

    return False

# ============================================================
# ADD FINDING MANUALLY
# ============================================================
def _add_manual_finding(findings):
    st.subheader("➕ Add New Finding")

    title = st.text_input("Title")
    severity = st.selectbox(
        "Severity", ["Critical", "High", "Moderate", "Low", "Informational"]
    )
    host = st.text_input("Host")
    port = st.text_input("Port")
    protocol = st.text_input("Protocol")

    description = st.text_area("Description", height=120)
    impact = st.text_area("Impact", height=120)
    recommendation = st.text_area("Recommendation", height=120)
    code = st.text_area("Code / Output", height=200)

    images = []
    new_imgs = st.file_uploader(
        "Upload Evidence Images",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    if new_imgs:
        for f in new_imgs:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            b64 = resize_image_b64(b64)
            images.append(b64)

    if st.button("Add Finding"):
        fid = next_finding_id(findings)
        findings.append(
            {
                "id": fid,
                "title": title,
                "severity": severity,
                "host": host,
                "port": port,
                "protocol": protocol,
                "description": description,
                "impact": impact,
                "recommendation": recommendation,
                "cvss": "",
                "cve": "",
                "code": code,
                "images": images,
            }
        )
        return True

    return False


# ============================================================
# FINDINGS TAB – MAIN FUNCTION
# ============================================================
def render_findings_tab(report_data: dict):
    st.header("🔍 Findings")

    if "findings" not in report_data:
        report_data["findings"] = []

    findings = report_data["findings"]

    # =======================================
    # IMPORT SECTION
    # =======================================
    st.subheader("📥 Import Findings")

    uploaded = st.file_uploader(
        "Upload Nessus / Nmap / OpenVAS / CSV / JSON",
        type=["nessus", "xml", "csv", "json", "nmap"],
    )

    if uploaded:
        try:
            imported = auto_parse_findings(uploaded.read(), uploaded.name)
            st.success(f"Detected {len(imported)} findings.")
            st.write("Preview (first 10):")
            for f in imported[:10]:
                st.write(f"**{f.get('title','Untitled')}** – {f.get('severity')}")

            severity_sel = st.multiselect(
                "Import only severities:", 
                ["Critical", "High", "Moderate", "Low", "Informational"],
                default=["Critical", "High", "Moderate", "Low", "Informational"],
            )
            severity_sel = set(severity_sel)

            if st.button("Import Findings Now"):
                for f in imported:
                    if f.get("severity") not in severity_sel:
                        continue

                    f["id"] = next_finding_id(findings)
                    f.setdefault("images", [])
                    findings.append(f)

                renumber_findings(findings)
                st.success("Import complete.")
                st.rerun()

        except Exception as e:
            st.error(f"Parser error: {e}")

    st.markdown("---")

    # =======================================
    # ADD MANUAL FINDING
    # =======================================
    if _add_manual_finding(findings):
        renumber_findings(findings)
        st.rerun()

    st.markdown("---")

    # =======================================
    # FILTER BY SEVERITY
    # =======================================
    st.subheader("Filter & List Findings")

    sev_filter = st.multiselect(
        "Show only severities:",
        ["Critical", "High", "Moderate", "Low", "Informational"],
        default=["Critical", "High", "Moderate", "Low", "Informational"],
    )

    filtered = [f for f in findings if f.get("severity") in sev_filter]

    # =======================================
    # LIST FINDINGS
    # =======================================
    for idx, f in enumerate(filtered):
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            sev = f.get("severity", "Informational")
            st.markdown(
                f"""
                <div style="padding:6px;
                            border-radius:6px;
                            margin-top:8px;
                            background:{SEVERITY_COLORS.get(sev,'#999')};
                            color:white;">
                    <b>{sev}</b> – {f.get("title", "Untitled Finding")}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            if st.button("Edit", key=f"edit_{idx}"):
                st.session_state["edit_index"] = idx

            if st.button("Delete", key=f"del_{idx}"):
                findings.pop(idx)
                renumber_findings(findings)
                st.rerun()

        # IF EDITING THIS FINDING
        if st.session_state.get("edit_index") == idx:
            st.markdown("### ✏️ Edit Finding")
            if _edit_finding_modal(f, idx):
                renumber_findings(findings)
                st.session_state["edit_index"] = None
                st.rerun()

    return report_data
