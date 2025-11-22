import streamlit as st
from util.helpers import resize_image_b64
import base64


def _ensure(report_data: dict):
    if "detailed_walkthrough" not in report_data or not isinstance(report_data["detailed_walkthrough"], list):
        report_data["detailed_walkthrough"] = []


def render_detailed_walkthrough_tab(report_data: dict):
    _ensure(report_data)
    items = report_data["detailed_walkthrough"]

    # Track the item being edited
    if "dw_edit_idx" not in st.session_state:
        st.session_state["dw_edit_idx"] = None

    st.subheader("🧩 Detailed Walkthrough (8.x)")

    # ----------------------------------------------------------------
    # ADD NEW STEP
    # ----------------------------------------------------------------
    st.markdown("### ➕ Add Walkthrough Step")

    with st.form("dw_add_form"):
        name = st.text_input("Title / Name", key="dw_add_name")
        description = st.text_area("Description", height=120, key="dw_add_desc")
        code = st.text_area("Code / Terminal Output (optional)", height=120, key="dw_add_code")

        imgs = st.file_uploader(
            "Upload Images / Evidence (optional)",
            type=["png", "jpg", "jpeg"],
            accept_multiple_files=True,
            key="dw_add_imgs",   # FIXED UNIQUE KEY
        )

        submit = st.form_submit_button("Add Walkthrough Step")
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
            st.success("Walkthrough step added.")
            st.rerun()

    st.markdown("---")

    # ----------------------------------------------------------------
    # LIST EXISTING
    # ----------------------------------------------------------------
    st.markdown("### 📑 Existing Walkthrough Steps")

    if not items:
        st.info("No walkthrough steps added.")
        return report_data

    for idx, item in enumerate(items):
        with st.expander(f"8.{idx+1} — {item.get('name','Untitled')}"):
            st.markdown(f"#### {item['name']}")

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
                    except:
                        pass

            col1, col2 = st.columns(2)

            # EDIT
            if col1.button("✏ Edit", key=f"dw_edit_btn_{idx}"):
                st.session_state["dw_edit_idx"] = idx
                st.rerun()

            # DELETE
            if col2.button("🗑 Delete", key=f"dw_del_btn_{idx}"):
                items.pop(idx)
                st.success("Walkthrough step removed.")
                st.rerun()

        # ----------------------------------------------------------------
        # EDIT MODAL
        # ----------------------------------------------------------------
        if st.session_state["dw_edit_idx"] == idx:
            with st.dialog(f"Edit 8.{idx+1} — {item['name']}"):

                new_name = st.text_input("Title / Name", item["name"], key=f"dw_edit_name_{idx}")
                new_desc = st.text_area("Description", item["description"], height=120, key=f"dw_edit_desc_{idx}")
                new_code = st.text_area("Code / Output", item["code"], height=120, key=f"dw_edit_code_{idx}")

                new_imgs = st.file_uploader(
                    "Attach more images (optional)",
                    type=["png", "jpg", "jpeg"],
                    accept_multiple_files=True,
                    key=f"dw_edit_imgs_{idx}",   # FIXED UNIQUE KEY
                )

                if st.button("💾 Save Changes", key=f"dw_save_btn_{idx}"):
                    item["name"] = new_name
                    item["description"] = new_desc
                    item["code"] = new_code

                    if new_imgs:
                        for img in new_imgs:
                            raw = img.read()
                            b64 = resize_image_b64(raw)
                            item["images"].append(b64)

                    st.session_state["dw_edit_idx"] = None
                    st.success("Changes saved.")
                    st.rerun()

                if st.button("Cancel", key=f"dw_cancel_btn_{idx}"):
                    st.session_state["dw_edit_idx"] = None
                    st.rerun()

    return report_data
