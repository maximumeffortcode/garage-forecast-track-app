import os
from datetime import datetime, date
import pandas as pd
import requests
import streamlit as st

# Configure these via environment variables or paste directly for quick tests
WEB_APP_URL = os.getenv("GS_WEBAPP_URL", "PASTE_WEB_APP_URL_HERE")  # ends with /exec
SHARED_TOKEN = os.getenv("GS_SHARED_TOKEN", "CHANGE_ME")

st.title("Garage Door Forecast Logger (Google Sheets via Apps Script)")

with st.form("entry_form", clear_on_submit=True):
    project_name = st.text_input("Project Name")
    lot_number   = st.text_input("Lot Number")
    expected     = st.date_input("Expected Install Date", value=date.today())
    status       = st.text_area("Recent Job Status Update")
    submitted    = st.form_submit_button("Append Row")

if submitted:
    if not project_name.strip():
        st.error("Project Name is required.")
    elif not lot_number.strip():
        st.error("Lot Number is required.")
    else:
        payload = {
            "projectName": project_name.strip(),
            "lotNumber": lot_number.strip(),
            "expectedInstallDate": pd.to_datetime(expected).date().isoformat(),
            "statusUpdate": status.strip(),
        }
        try:
            r = requests.post(f"{WEB_APP_URL}?token={SHARED_TOKEN}", json=payload, timeout=15)
            if r.ok and r.text.strip() == "OK":
                st.success("Saved to Google Sheets ✅")
            else:
                st.error(f"Write failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Network error: {e}")

st.divider()
st.subheader("Most recent entries")

# Optional viewer: read back from Apps Script (JSON)
try:
    r = requests.get(f"{WEB_APP_URL}?token={SHARED_TOKEN}", timeout=15)
    if r.ok:
        data = r.json()
        if data:
            df = pd.DataFrame(data)
            # Convert Timestamp to readable string if it's a Google serial date
            st.dataframe(df.tail(10), use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                               file_name="forecast_log.csv", mime="text/csv")
        else:
            st.info("No rows yet. Add your first entry above.")
    else:
        st.caption(f"Viewer error: {r.status_code} {r.text}")
except Exception as e:
    st.caption(f"Viewer error: {e}")
