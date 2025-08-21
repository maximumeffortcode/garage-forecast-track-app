on
import os
from datetime import date
import pandas as pd
import requests
import streamlit as st

WEB_APP_URL = st.secrets["GS_WEBAPP_URL"]
SHARED_TOKEN = st.secrets["GS_SHARED_TOKEN"]

st.set_page_config(page_title="Garage Forecast Logger", page_icon="🗓️", layout="wide")
st.title("Garage Door Forecast Logger (Projects → Tabs)")

# --- Helpers ---
def list_tabs() -> list[str]:
    try:
        r = requests.get(f"{WEB_APP_URL}?token={SHARED_TOKEN}&listSheets=1", timeout=15)
        if r.ok:
            return r.json()
        else:
            st.caption(f"List error: {r.status_code} {r.text}")
    except Exception as e:
        st.toast(f"Couldn't list tabs: {e}", icon="⚠️")
    return []

def fetch_tab_records(tab: str) -> pd.DataFrame:
    try:
        r = requests.get(f"{WEB_APP_URL}?token={SHARED_TOKEN}&projectTab={requests.utils.quote(tab)}", timeout=20)
        if r.ok:
            data = r.json()
            return pd.DataFrame(data)
        else:
            st.caption(f"Viewer error: {r.status_code} {r.text}")
    except Exception as e:
        st.caption(f"Viewer error: {e}")
    return pd.DataFrame(columns=[
        "Timestamp","Project Name","Lot Number","Expected Install Date","Recent Job Status Update"
    ])

def fetch_dashboard() -> pd.DataFrame:
    try:
        r = requests.get(f"{WEB_APP_URL}?token={SHARED_TOKEN}&dashboard=1", timeout=30)
        if r.ok:
            return pd.DataFrame(r.json())
        else:
            st.caption(f"Dashboard error: {r.status_code} {r.text}")
    except Exception as e:
        st.caption(f"Dashboard error: {e}")
    return pd.DataFrame(columns=[
        "Project Tab","Timestamp","Project Name","Lot Number","Expected Install Date","Recent Job Status Update"
    ])

# --- Sidebar: project/tab picking ---
with st.sidebar:
    st.header("Project (Sheet Tab)")
    existing_tabs = list_tabs()
    if not existing_tabs:
        st.info("No tabs found yet. The app will create one when you submit.", icon="ℹ️")
    mode = st.radio("Pick or create:", ["Choose existing", "Create new"], horizontal=True)
    if mode == "Choose existing" and existing_tabs:
        project_tab = st.selectbox("Existing tabs", existing_tabs)
    else:
        project_tab = st.text_input("New tab name", placeholder="e.g., Project_A").strip()
        if project_tab == "":
            st.warning("Enter a new tab name or switch to 'Choose existing'.", icon="⚠️")

# --- Main form ---
with st.form("entry_form", clear_on_submit=True):
    project_name = st.text_input("Project Name")
    lot_number   = st.text_input("Lot Number")
    expected     = st.date_input("Expected Install Date", value=date.today())
    status       = st.text_area("Recent Job Status Update")
    submitted    = st.form_submit_button("Append to Tab")

if submitted:
    if not project_tab:
        st.error("Select or enter a Project (tab) name.")
    elif not project_name.strip():
        st.error("Project Name is required.")
    elif not lot_number.strip():
        st.error("Lot Number is required.")
    else:
        payload = {
            "projectTab": project_tab,
            "projectName": project_name.strip(),
            "lotNumber": lot_number.strip(),
            "expectedInstallDate": pd.to_datetime(expected).date().isoformat(),
            "statusUpdate": status.strip(),
        }
        try:
            r = requests.post(f"{WEB_APP_URL}?token={SHARED_TOKEN}", json=payload, timeout=20)
            if r.ok and r.text.strip() == "OK":
                st.success(f"Saved to tab '{project_tab}' ✅")
            else:
                st.error(f"Write failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Network error: {e}")

st.divider()

# --- Dashboard controls ---
st.subheader("Dashboard")
col1, col2 = st.columns([1, 3], gap="large")
with col1:
    if st.button("Refresh Dashboard", use_container_width=True):
        try:
            r = requests.post(f"{WEB_APP_URL}?token={SHARED_TOKEN}", json={"action": "refreshDashboard"}, timeout=40)
            if r.ok and r.text.strip() == "OK":
                st.success("Dashboard rebuilt ✅")
            else:
                st.error(f"Refresh failed: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Network error: {e}")

with col2:
    dash_df = fetch_dashboard()
    if not dash_df.empty:
        st.dataframe(dash_df.tail(50), use_container_width=True, height=380)
        st.download_button(
            "Download dashboard (CSV)",
            dash_df.to_csv(index=False).encode("utf-8"),
            file_name="dashboard.csv",
            mime="text/csv",
        )
    else:
        st.caption("No dashboard data yet. Click Refresh Dashboard after adding entries.")

st.divider()
st.subheader("Tab preview")

if 'project_tab' in locals() and project_tab:
    df = fetch_tab_records(project_tab)
    if not df.empty:
        st.dataframe(df.tail(20), use_container_width=True)
        st.download_button(
            "Download this tab (CSV)",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"{project_tab}.csv",
            mime="text/csv",
        )
    else:
        st.caption("No rows yet on this tab.")
else:
    st.caption("Pick or create a tab to preview entries.")
