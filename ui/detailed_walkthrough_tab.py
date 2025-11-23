import streamlit as st
from util.helpers import resize_image_b64
import base64


def _ensure(report_data: dict):
    if "detailed_walkthrough" not in report_data or not isinstance(report_data["detailed_walkthrough"], list):
        report_data["detailed_walkthrough"] = []


import streamlit as st
import base64
from util.helpers import resize_image_b64


def render_detailed_walkthrough_tab(report_data: dict):
    """
    UI Tab for section 8.0 Detailed Walkthrough.
    Allows: Add steps, list steps, edit steps, delete steps.
    """

    st.header("🔍 8.0 Detailed Walkthrough")

    # Ensure data structure exists
    if "detailed_walkthrough" not in report_data:
        report_data["detailed_walkthrough"] = []

    walkthrough = report_data["detailed_walkthrough"]

    # ======================================================
    # 1. ADD NEW STEP
    # ======================================================
    st.subheader("➕ Add New Walkthrough Step")

    new_title = st.text_input("Title", key="dw_new_title")
    new_desc = st.text_area("Description", height=150, key="dw_new_desc")
    new_code = st.text_area("Code Block (optional)", height=120, key="dw_new_code")

    new_imgs = st.file_uploader(
        "Upload Images (optional)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=True,
        key="dw_new_imgs",
    )

    new_images_b64 = []
    if new_imgs:
        for img in new_imgs:
            raw = img.read()
            b64 = resize_image_b64(raw)
            new_images_b64.append(b64)

    if st.button("Add Step", key="dw_add_btn"):
        if new_title.strip():
            walkthrough.append(
                {
                    "name": new_title.strip(),
                    "description": new_desc,
                    "code": new_code,
                    "images": new_images_b64,
                }
            )
            st.success("Walkthrough step added!")
            st.rerun()
        else:
            st.error("Please enter a title.")

    st.markdown("---")

    # ======================================================
    # 2. LIST EXISTING STEPS
    # ======================================================
    st.subheader("📄 Existing Walkthrough Steps")

    if not walkthrough:
        st.info("No walkthrough steps added yet.")
        return report_data

    for idx, item in enumerate(walkthrough):
        st.markdown(f"### **8.{idx+1} — {item['name']}**")

        # Description
        if item["description"]:
            st.markdown(item["description"].replace("\n", "<br/>"), unsafe_allow_html=True)

        # Images (display only)
        if item.get("images"):
            for b64 in item["images"]:
                try:
                    st.image(base64.b64decode(b64), use_container_width=True)
                except:
                    pass

        # Code preview
        if item.get("code"):
            st.code(item["code"], language="bash")

        # Buttons: Edit / Delete
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("✏️ Edit", key=f"dw_edit_btn_{idx}"):
                st.session_state["dw_edit_index"] = idx
                st.rerun()

        with col2:
            if st.button("🗑 Delete", key=f"dw_delete_btn_{idx}"):
                del walkthrough[idx]
                st.success("Deleted.")
                st.rerun()

        st.markdown("---")

    # ======================================================
    # 3. EDIT MODAL
    # ======================================================
    if st.session_state.get("dw_edit_index") is not None:
        idx = st.session_state["dw_edit_index"]
        item = walkthrough[idx]

        with st.dialog(f"Edit Walkthrough Step 8.{idx+1} — {item['name']}"):

            # Title
            item["name"] = st.text_input(
                "Title",
                item["name"],
                key=f"dw_edit_title_{idx}",
            )

            # Description
            item["description"] = st.text_area(
                "Description",
                item["description"],
                height=150,
                key=f"dw_edit_desc_{idx}",
            )

            # Code
            item["code"] = st.text_area(
                "Code Block (optional)",
                item.get("code", ""),
                height=120,
                key=f"dw_edit_code_{idx}",
            )

            # Existing images
            st.markdown("### Existing Images")
            if item.get("images"):
                for i, b64 in enumerate(item["images"]):
                    try:
                        st.image(base64.b64decode(b64), use_container_width=True)
                    except:
                        pass

                    if st.button(f"🗑 Delete Image {i+1}", key=f"dw_edit_delete_img_{idx}_{i}"):
                        del item["images"][i]
                        st.rerun()

            # Add new images
            st.markdown("### Add More Images")
            edit_imgs = st.file_uploader(
                "Upload additional images",
                type=["png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key=f"dw_edit_uploader_{idx}",
            )

            if edit_imgs:
                for img in edit_imgs:
                    raw = img.read()
                    b64 = resize_image_b64(raw)
                    item["images"].append(b64)

            st.markdown("---")

            # SAVE
            if st.button("💾 Save Changes", key=f"dw_save_{idx}"):
                st.session_state["dw_edit_index"] = None
                st.success("Updated successfully.")
                st.rerun()

            # CANCEL
            if st.button("❌ Cancel", key=f"dw_cancel_{idx}"):
                st.session_state["dw_edit_index"] = None
                st.rerun()

    return report_data
