#ui/detailed_walkthrough_tab.py
import streamlit as st
import base64
from util.helpers import resize_image_b64


def render_detailed_walkthrough_tab(report_data: dict):

    st.header("ðŸ” 8.0 Detailed Walkthrough")
    st.caption("Add detailed attack chains, exploit steps, lateral movement, screenshots, code samples.")

    # Ensure structure
    if "detailed_walkthrough" not in report_data or not isinstance(report_data["detailed_walkthrough"], list):
        report_data["detailed_walkthrough"] = []

    walkthrough = report_data["detailed_walkthrough"]

    # ======================================================
    # ADD NEW STEP
    # ======================================================
    with st.expander("âž• Add Walkthrough Step", expanded=False):

        title = st.text_input("Title", key="dw_new_title")
        description = st.text_area("Description (multiline)", key="dw_new_desc")
        code = st.text_area("Code Block (optional)", key="dw_new_code")

        images_upload = st.file_uploader(
            "Upload screenshots",
            accept_multiple_files=True,
            type=["png", "jpg", "jpeg"],
            key="dw_new_images",
        )

        if st.button("Add Walkthrough Step", key="dw_add_btn"):
            images_b64 = []
            if images_upload:
                for img in images_upload:
                    raw = img.read()
                    b64 = resize_image_b64(raw)
                    images_b64.append(b64)

            walkthrough.append({
                "name": title.strip() or "Untitled Step",
                "description": description,
                "code": code,
                "images": images_b64,
            })

            st.success("Step added!")
            st.rerun()

    st.markdown("---")

    # ======================================================
    # LIST EXISTING STEPS
    # ======================================================
    st.subheader("ðŸ“„ Existing Walkthrough Steps")

    if not walkthrough:
        st.info("No steps added yet.")
        return report_data

    for idx, step in enumerate(walkthrough):

        box = st.container(border=True)
        with box:
            st.markdown(f"### **8.{idx+1} â€“ {step['name']}**")

            if step.get("description"):
                st.markdown(step["description"].replace("\n", "<br>"), unsafe_allow_html=True)

            if step.get("code"):
                st.code(step["code"], language="bash")

            if step.get("images"):
                st.markdown("**Images:**")
                for b64 in step["images"]:
                    try:
                        st.image(base64.b64decode(b64), width="stretch")
                    except:
                        pass

            col1, col2 = st.columns(2)
            with col1:
                if st.button("âœï¸ Edit", key=f"dw_edit_btn_{idx}"):
                    st.session_state["dw_edit_index"] = idx
                    st.rerun()

            with col2:
                if st.button("ðŸ—‘ Delete", key=f"dw_del_btn_{idx}"):
                    del walkthrough[idx]
                    st.success("Deleted.")
                    st.rerun()

        st.markdown("---")

    # ======================================================
    # EDIT MODAL (SIMULATED)
    # ======================================================
    if st.session_state.get("dw_edit_index") is not None:

        idx = st.session_state["dw_edit_index"]

        # Safety
        if idx < 0 or idx >= len(walkthrough):
            st.session_state["dw_edit_index"] = None
            return report_data

        step = walkthrough[idx]

        with st.container(border=True):
            st.markdown(f"## âœï¸ Edit Walkthrough Step 8.{idx+1}")

            # Title
            step["name"] = st.text_input(
                "Title",
                step["name"],
                key=f"dw_edit_title_{idx}",
            )

            # Description
            step["description"] = st.text_area(
                "Description",
                step.get("description", ""),
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
                for i, b64 in enumerate(step["images"]):
                    try:
                        st.image(base64.b64decode(b64), width="stretch")
                    except:
                        pass

                    if st.button(f"ðŸ—‘ Delete Image {i+1}", key=f"dw_del_img_{idx}_{i}"):
                        del step["images"][i]
                        st.rerun()

            # Add new images
            st.markdown("### Add More Images")
            new_imgs = st.file_uploader(
                "Upload screenshots",
                accept_multiple_files=True,
                type=["png", "jpg", "jpeg"],
                key=f"dw_edit_new_images_{idx}",
            )

            if new_imgs:
                for img in new_imgs:
                    raw = img.read()
                    b64 = resize_image_b64(raw)
                    step["images"].append(b64)

            st.markdown("---")

            colA, colB = st.columns(2)
            with colA:
                if st.button("ðŸ’¾ Save Changes", key=f"dw_save_{idx}"):
                    st.session_state["dw_edit_index"] = None
                    st.success("Updated.")
                    st.rerun()

            with colB:
                if st.button("âŒ Cancel", key=f"dw_cancel_{idx}"):
                    st.session_state["dw_edit_index"] = None
                    st.rerun()

    return report_data
