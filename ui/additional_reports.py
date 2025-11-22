# ui/additional_reports.py

import base64
import streamlit as st
from util.helpers import resize_image_b64


def _ensure_additional(report_data: dict):
    if "additional_reports" not in report_data or not isinstance(report_data["additional_reports"], list):
        report_data["additional_reports"] = []


def render_additional_reports(report_data: dict):
    _ensure_additional(report_data)
    items = report_data["additional_reports"]

    if "edit_additional_idx" not in st.session_state:
        st.session_state["edit_additional_idx"] = None

    st.subheader("📄 Additional Reports & Scans")

    # -------------------------------------------------------
    # ADD NEW
    # -------------------------------------------------------
    st.markdown("### ➕ Add Additional Report / Scan")

    with st.form("add_additional_report_form"):
        name = st.text_input("Title / Name")
        description = st.text_area("Description", height=120)
        code = st.text_area("Code / Terminal Output (optional)", height=120)

        imgs = st.file_uploader(
            "Upload Images / Evidence (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="add_additional_imgs",
        )

        submit = st.form_submit_button("Add Additional Report")
        if submit:
            entry = {
                "name": name or "Untitled",
                "description": description,
                "code": code,
                "images": [],
            }
            if imgs:
                for img in imgs:
                    b64 = base64.b64encode(img.read()).decode()
                    b64 = resize_image_b64(b64)
                    entry["images"].append(b64)
            items.append(entry)
            st.success("Additional report added.")
            st.rerun()

    st.markdown("---")

    # -------------------------------------------------------
    # LIST EXISTING
    # -------------------------------------------------------
    st.markdown("### 📑 Existing Additional Reports")

    if not items:
        st.info("No additional reports added.")
        return

    for idx, item in enumerate(items):
        with st.expander(f"{idx+1}. {item.get('name','Untitled')}"):
            st.markdown(f"#### {item.get('name','')}")
            if item.get("description"):
                st.markdown("**Description**")
                st.write(item["description"])

            if item.get("code"):
                st.markdown("**Code / Output**")
                st.code(item["code"], language="bash")

            if item.get("images"):
                st.markdown("**Images**")
                for b64 in item["images"]:
                    try:
                        st.image(base64.b64decode(b64), use_container_width=True)
                    except Exception:
                        continue

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit", key=f"edit_add_{idx}"):
                    st.session_state["edit_additional_idx"] = idx
                    st.rerun()
            with col2:
                if st.button("🗑️ Delete", key=f"del_add_{idx}"):
                    items.pop(idx)
                    st.success("Additional report removed.")
                    st.rerun()

            # EDIT AREA
            if st.session_state.get("edit_additional_idx") == idx:
                st.markdown("---")
                st.markdown("### ✏️ Edit Additional Report")
                with st.form(f"edit_additional_form_{idx}", clear_on_submit=False):
                    new_name = st.text_input("Title / Name", item.get("name",""))
                    new_desc = st.text_area("Description", item.get("description",""), height=120)
                    new_code = st.text_area("Code / Output", item.get("code",""), height=120)

                    new_imgs = st.file_uploader(
                        "Attach more images (optional)",
                        type=["png","jpg","jpeg"],
                        accept_multiple_files=True,
                        key=f"edit_add_imgs_{idx}",
                    )

                    save = st.form_submit_button("💾 Save Changes")
                    if save:
                        item["name"] = new_name
                        item["description"] = new_desc
                        item["code"] = new_code
                        if new_imgs:
                            for img in new_imgs:
                                b64 = base64.b64encode(img.read()).decode()
                                b64 = resize_image_b64(b64)
                                item["images"].append(b64)
                        st.session_state["edit_additional_idx"] = None
                        st.success("Changes saved.")
                        st.rerun()
