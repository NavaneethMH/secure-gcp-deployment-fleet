import streamlit as st

st.set_page_config(
    page_title="Secure GCP Deployment Fleet",
    page_icon="🚀",
)

st.title("Secure GCP Deployment Fleet")
st.subheader("Cloud Run Deployment Test")

st.success("The application is running successfully on Google Cloud Run.")

st.write(
    "This service was containerized by the Build Agent, "
    "published by the Registry Agent, and deployed by the Hosting Agent."
)

st.info("Phase 3C deployment verification successful.")
