import streamlit as st
import base64
from util.helpers import resize_image_b64


def render_detailed_walkthrough_tab(report_data: dict):
    """
    UI Tab for section 8.0 Detailed Walkthrough.
    Allows: Add steps, list steps, edit steps, delete steps.
    """

    st.header("🔍 8.0 Detailed Walkthrough")
    st.caption("Add detailed attack chains, lateral movement paths, exploit steps, screenshots and code samples.")

    # Ensure data structure exists
    if "detailed_walkthrough" not in report_data or not isinstance(report_data["detailed_walkthrough"], list):
        report_data["detailed_walkthrough"] = []

    walkthrough = report_data["detailed_walkthrough"]

    # ======================================================
    # 1. ADD NEW STEP
    # ======================================================
    st.subheader("➕ Add Walkthrough Step")

    with st.expander("Add Walkthrough Step", expanded=False):
        title = st.text_input("Title", key="dw_new_title")
        description = st.text_area("Description (multiline)", key="dw_new_desc")
        code = st.text_area("Code Block (optional)", key="dw_new_code")

        images_upload = st.file_uploader(
            "Upload Screenshots",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="dw_new_images",
        )

        if st.button("Add Walkthrough Step", key="dw_add_btn"):
            images_b64 = []
            if images_upload:
                for img in images_upload:
                    # citim bytes -> redimensionăm -> stocăm ca base64 text
                    raw = img.read()
                    b64 = resize_image_b64(raw, max_size=900)
                    images_b64.append(b64)

            walkthrough.append(
                {
                    "name": title.strip() or "Untitled Step",
                    "description": description,
                    "code": code,
                    "images": images_b64,
                }
            )

            st.success("Walkthrough step added!")
            st.rerun()

    st.markdown("---")

    # ======================================================
    # 2. LIST EXISTING STEPS
    # ======================================================
    st.subheader("📄 Existing Walkthrough Steps")

    if not walkthrough:
        st.info("No walkthrough steps added yet.")
        return report_data

    for idx, step in enumerate(walkthrough):
        box = st.container(border=True)

        with box:
            st.markdown(f"### **8.{idx+1} – {step['name']}**")

            if step.get("description"):
                st.markdown(step["description"].replace("\n", "<br/>"), unsafe_allow_html=True)

            if step.get("code"):
                st.code(step["code"], language="bash")

            if step.get("images"):
                for img_b64 in step["images"]:
                    try:
                        # img_b64 este string base64 → decodăm în bytes
                        img_bytes = base64.b64decode(img_b64)
                        st.image(img_bytes, use_column_width=True)
                    except Exception:
                        continue

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✏️ Edit", key=f"dw_edit_btn_{idx}"):
                    st.session_state["dw_edit_index"] = idx
                    st.rerun()

            with col2:
                if st.button("🗑 Delete", key=f"dw_del_btn_{idx}"):
                    del walkthrough[idx]
                    st.success("Walkthrough step deleted.")
                    st.rerun()

        st.markdown("---")

    # ======================================================
    # 3. EDIT MODAL
    # ======================================================
    if st.session_state.get("dw_edit_index") is not None:
        idx = st.session_state["dw_edit_index"]
        # dacă între timp s-a șters ceva, protejăm indexul
        if idx < 0 or idx >= len(walkthrough):
            st.session_state["dw_edit_index"] = None
            return report_data

        step = walkthrough[idx]

        with st.dialog(f"Edit Walkthrough Step 8.{idx+1} — {step['name']}"):

            # Title
            step["name"] = st.text_input(
                "Title",
                step["name"],
                key=f"dw_edit_title_{idx}",
            )

            # Description
            step["description"] = st.text_area(
                "Description",
                step["description"],
                height=150,
                key=f"dw_edit_desc_{idx}",
            )

            # Code
            step["code"] = st.text_area(
                "Code Block (optional)",
                step.get("code", ""),
                height=120,
                key=f"dw_edit_code_{idx}",
            )

            # Existing images
            st.markdown("### Existing Images")
            if step.get("images"):
                for i, img_b64 in enumerate(step["images"]):
                    try:
                        img_bytes = base64.b64decode(img_b64)
                        st.image(img_bytes, use_column_width=True)
                    except Exception:
                        continue

                    if st.button(f"🗑 Delete Image {i+1}", key=f"dw_edit_del_img_{idx}_{i}"):
                        del step["images"][i]
                        st.rerun()

            # Add new images
            st.markdown("### Add More Images")
            edit_imgs = st.file_uploader(
                "Upload additional screenshots",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"dw_edit_images_{idx}",
            )

            if edit_imgs:
                for img in edit_imgs:
                    raw = img.read()
                    b64 = resize_image_b64(raw, max_size=900)
                    step["images"].append(b64)

            st.markdown("---")

            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("💾 Save Changes", key=f"dw_save_{idx}"):
                    st.session_state["dw_edit_index"] = None
                    st.success("Updated successfully.")
                    st.rerun()
            with col_s2:
                if st.button("❌ Cancel", key=f"dw_cancel_{idx}"):
                    st.session_state["dw_edit_index"] = None
                    st.rerun()

    return report_data
