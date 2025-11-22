import streamlit as st
from util.helpers import resize_image_b64
import base64


def render_detailed_walkthrough_tab(report_data: dict):
    st.header("?? Detailed Walkthrough (8.x)")
    st.caption("Add detailed attack chains, lateral movement paths, exploit steps, screenshots and code samples.")

    if "detailed_walkthrough" not in report_data:
        report_data["detailed_walkthrough"] = []

    walkthrough = report_data["detailed_walkthrough"]

    # ---------------- ADD NEW ----------------
    st.subheader("? Add Walkthrough Step")

    with st.expander("Add Walkthrough Step", expanded=False):
        title = st.text_input("Title", key="dw_new_title")
        description = st.text_area("Description (multiline)", key="dw_new_desc")
        code = st.text_area("Code Block (optional)", key="dw_new_code")
        images_upload = st.file_uploader(
            "Upload Screenshots",
            accept_multiple_files=True,
            key="dw_new_images"
        )

        if st.button("Add Walkthrough Step", key="dw_add_btn"):
            images_b64 = []
            if images_upload:
                for img in images_upload:
                    images_b64.append(resize_image_b64(img.read(), max_w=1400))

            walkthrough.append({
                "title": title.strip() or "Untitled Step",
                "description": description,
                "code": code,
                "images": images_b64
            })

            st.success("Walkthrough step added!")
            st.rerun()

    # ---------------- EXISTING ----------------
    st.markdown("---")
    st.subheader("?? Existing Walkthrough Steps")

    if not walkthrough:
        st.info("No walkthrough steps added yet.")
        return report_data

    for idx, step in enumerate(walkthrough):
        box = st.container(border=True)

        with box:
            st.write(f"### **8.{idx+1} – {step['title']}**")
            st.write(step["description"])

            if step.get("code"):
                st.code(step["code"], language="bash")

            if step.get("images"):
                for img_b64 in step["images"]:
                    st.image(base64.b64decode(img_b64), use_column_width=True)

            col1, col2 = st.columns(2)

            if col1.button("? Edit", key=f"dw_edit_btn_{idx}"):
                st.session_state["edit_walkthrough"] = idx
                st.rerun()

            if col2.button("?? Delete", key=f"dw_del_btn_{idx}"):
                del walkthrough[idx]
                st.rerun()

        st.markdown("---")

    # ---------------- EDIT MODAL ----------------
    if "edit_walkthrough" in st.session_state:
        idx = st.session_state["edit_walkthrough"]
        step = walkthrough[idx]

        with st.modal(f"Edit 8.{idx+1} — {step['title']}"):

            new_title = st.text_input("Title", step["title"], key=f"dw_edit_title_{idx}")
            new_description = st.text_area("Description", step["description"], key=f"dw_edit_desc_{idx}")
            new_code = st.text_area("Code Block", step["code"], key=f"dw_edit_code_{idx}")

            st.write("Existing Images:")
            for img_b64 in step.get("images", []):
                st.image(base64.b64decode(img_b64), use_column_width=True)

            new_images = st.file_uploader(
                "Upload Additional Screenshots",
                accept_multiple_files=True,
                key=f"dw_edit_images_{idx}"
            )

            if st.button("Save Changes", key=f"dw_edit_save_{idx}"):
                step["title"] = new_title
                step["description"] = new_description
                step["code"] = new_code

                if new_images:
                    for img in new_images:
                        step["images"].append(resize_image_b64(img.read(), max_w=1400))

                st.session_state.pop("edit_walkthrough")
                st.success("Walkthrough step updated!")
                st.rerun()

            if st.button("Cancel", key=f"dw_edit_cancel_{idx}"):
                st.session_state.pop("edit_walkthrough")
                st.rerun()

    return report_data