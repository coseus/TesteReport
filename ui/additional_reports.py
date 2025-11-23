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

    st.subheader("ðŸ“„ Additional Reports & Scans")

    # -------------------------------------------------------
    # ADD NEW
    # -------------------------------------------------------
    st.markdown("### âž• Add Additional Report / Scan")

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
                    raw = img.read()
                    b64 = resize_image_b64(raw)
                    entry["images"].append(b64)
            items.append(entry)
            st.success("Additional report added.")
            st.rerun()

    st.markdown("---")

    # -------------------------------------------------------
    # LIST EXISTING
    # -------------------------------------------------------
    st.markdown("### ðŸ“‘ Existing Additional Reports")

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
                        st.image(base64.b64decode(b64), width="stretch")
                    except Exception:
                        continue

            col1, col2 = st.columns(2)
            with col1:
                if st.button("âœï¸ Edit", key=f"edit_add_{idx}"):
                    st.session_state["edit_additional_idx"] = idx
                    st.rerun()

            with col2:
                if st.button("ðŸ—‘ï¸ Delete", key=f"del_add_{idx}"):
                    items.pop(idx)
                    st.success("Additional report removed.")
                    st.rerun()

            # ======================================================
            # EDIT MODE
            # ======================================================
            if st.session_state.get("edit_additional_idx") == idx:
                st.markdown("---")
                st.markdown("### âœï¸ Edit Additional Report")

                with st.form(f"edit_additional_form_{idx}", clear_on_submit=False):

                    new_name = st.text_input("Title / Name", item.get("name",""), key=f"edit_name_{idx}")
                    new_desc = st.text_area("Description", item.get("description",""), height=120, key=f"edit_desc_{idx}")
                    new_code = st.text_area("Code / Output", item.get("code",""), height=120, key=f"edit_code_{idx}")

                    # ------------------------------
                    # EXISTING IMAGES + DELETE BUTTON
                    # ------------------------------
                    st.markdown("### Existing Images")

                    if item.get("images"):
                        for img_idx, b64 in enumerate(item["images"]):

                            try:
                                st.image(base64.b64decode(b64), width="stretch")
                            except:
                                pass

                            if st.form_submit_button(f"ðŸ—‘ Delete Image {img_idx+1}", key=f"del_existing_img_{idx}_{img_idx}"):
                                del item["images"][img_idx]
                                st.success("Image deleted.")
                                st.session_state["edit_additional_idx"] = idx
                                st.rerun()

                    # ------------------------------
                    # ADD NEW IMAGES
                    # ------------------------------
                    st.markdown("### Add More Images")

                    new_imgs = st.file_uploader(
                        "Attach more images",
                        type=["png", "jpg", "jpeg"],
                        accept_multiple_files=True,
                        key=f"edit_add_imgs_{idx}",
                    )

                    if new_imgs:
                        for img in new_imgs:
                            raw = img.read()
                            b64 = resize_image_b64(raw)
                            item["images"].append(b64)

                    # ------------------------------
                    # SAVE / CANCEL
                    # ------------------------------
                    colA, colB = st.columns(2)

                    with colA:
                        if st.form_submit_button("ðŸ’¾ Save Changes", key=f"save_add_{idx}"):
                            item["name"] = new_name
                            item["description"] = new_desc
                            item["code"] = new_code
                            st.session_state["edit_additional_idx"] = None
                            st.success("Changes saved.")
                            st.rerun()

                    with colB:
                        if st.form_submit_button("âŒ Cancel", key=f"cancel_add_{idx}"):
                            st.session_state["edit_additional_idx"] = None
                            st.rerun()
