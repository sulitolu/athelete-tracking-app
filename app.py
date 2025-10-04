
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
import os
from utils import ai_daily_summary

st.set_page_config(page_title="Athlete Data App (MVP)", layout="wide")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

st.title("🏉 Athlete Data App — MVP")

def load_csv(path, cols):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for c in cols:
            if c not in df.columns: df[c] = np.nan
        return df[cols]
    else:
        return pd.DataFrame(columns=cols)

def save_csv(df, path):
    df.to_csv(path, index=False)

WELLNESS_COLS = [
    "Date (YYYY-MM-DD)","Sleep Hours","Sleep Quality (1-5)","HRV (ms, optional)",
    "Resting HR (bpm, optional)","Stress (1-5)","Soreness (1-5)","Mood (1-5)",
    "Body Weight (kg)","Body Fat % (optional)","Notes"
]
GPS_COLS = [
    "Date (YYYY-MM-DD)","Session Name","Duration (min)","Total Distance (m)",
    "HSR Distance (m)","VHSR Distance (m)","Top Speed (m/s)",
    "Accelerations >2.5 m/s^2","Accelerations >3.5 m/s^2","Max Accel (m/s^2)",
    "Player Load / Strain (optional)","RPE (1-10)","sRPE (RPE*Duration)","Notes"
]
GYM_COLS = [
    "Date (YYYY-MM-DD)","Lift","Set","Reps","Weight (kg)","Estimated 1RM (kg)","Velocity (m/s, optional)","Notes"
]
BODY_COLS = [
    "Date (YYYY-MM-DD)","Method (InBody/Caliper)","Weight (kg)","Body Fat %","SMM (kg)","Visceral Fat (optional)","Notes"
]
TESTS_COLS = ["Date (YYYY-MM-DD)","Test (Yo-Yo/MAS/30-15/3RM/CMJ etc.)","Score/Time/Level","Notes"]

w_path = os.path.join(DATA_DIR, "wellness.csv")
g_path = os.path.join(DATA_DIR, "gps.csv")
gym_path = os.path.join(DATA_DIR, "gym.csv")
b_path = os.path.join(DATA_DIR, "body.csv")
t_path = os.path.join(DATA_DIR, "tests.csv")

wellness = load_csv(w_path, WELLNESS_COLS)
gps = load_csv(g_path, GPS_COLS)
gym = load_csv(gym_path, GYM_COLS)
body = load_csv(b_path, BODY_COLS)
tests = load_csv(t_path, TESTS_COLS)

st.sidebar.header("📥 Import / Export")
up = st.sidebar.file_uploader("Import from Excel template", type=["xlsx"])
if up is not None:
    try:
        xls = pd.ExcelFile(up)
        wellness = xls.parse("1-Daily Wellness")
        gps = xls.parse("2-GPS Sessions")
        gym = xls.parse("3-Gym Log")
        body = xls.parse("4-Body Comp")
        tests = xls.parse("5-Tests")
        st.sidebar.success("Imported from Excel successfully.")
    except Exception as e:
        st.sidebar.error(f"Import error: {e}")

if st.sidebar.button("💾 Save All"):
    save_csv(wellness, w_path)
    save_csv(gps, g_path)
    save_csv(gym, gym_path)
    save_csv(body, b_path)
    save_csv(tests, t_path)
    st.sidebar.success("Saved to data/*.csv")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Home", "Wellness", "GPS", "Gym", "Body/Tests", "AI Summary"])

with tab2:
    st.subheader("Daily Wellness")
    with st.form("wellness_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            w_date = st.date_input("Date", value=date.today())
            sleep_hours = st.number_input("Sleep Hours", 0.0, 14.0, 7.0, 0.25)
            sleep_quality = st.slider("Sleep Quality (1-5)", 1, 5, 3)
            mood = st.slider("Mood (1-5)", 1, 5, 3)
        with c2:
            stress = st.slider("Stress (1-5)", 1, 5, 2)
            soreness = st.slider("Soreness (1-5)", 1, 5, 2)
            weight = st.number_input("Body Weight (kg)", 0.0, 300.0, 120.0, 0.1)
            bodyfat = st.number_input("Body Fat % (optional)", 0.0, 60.0, 0.0, 0.1)
        with c3:
            hrv = st.number_input("HRV (ms, optional)", 0.0, 300.0, 0.0, 1.0)
            rhr = st.number_input("Resting HR (bpm, optional)", 0.0, 220.0, 0.0, 1.0)
            notes = st.text_input("Notes", value="")

        submitted = st.form_submit_button("Add / Update")
        if submitted:
            row = {
                "Date (YYYY-MM-DD)": str(w_date),
                "Sleep Hours": sleep_hours,
                "Sleep Quality (1-5)": sleep_quality,
                "HRV (ms, optional)": hrv if hrv>0 else np.nan,
                "Resting HR (bpm, optional)": rhr if rhr>0 else np.nan,
                "Stress (1-5)": stress,
                "Soreness (1-5)": soreness,
                "Mood (1-5)": mood,
                "Body Weight (kg)": weight,
                "Body Fat % (optional)": bodyfat if bodyfat>0 else np.nan,
                "Notes": notes
            }
            mask = wellness["Date (YYYY-MM-DD)"] == row["Date (YYYY-MM-DD)"]
            if mask.any():
                wellness.loc[mask, :] = row
            else:
                wellness = pd.concat([wellness, pd.DataFrame([row])], ignore_index=True)
            st.success("Saved wellness entry (not yet persisted — click 'Save All' in sidebar).")
    st.dataframe(wellness)

with tab3:
    st.subheader("GPS Sessions")
    with st.form("gps_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="gps_date")
            session = st.text_input("Session Name", value="Training")
            duration = st.number_input("Duration (min)", 0.0, 300.0, 60.0, 1.0)
        with c2:
            dist = st.number_input("Total Distance (m)", 0.0, 50000.0, 4500.0, 50.0)
            hsr = st.number_input("HSR Distance (m)", 0.0, 20000.0, 100.0, 10.0)
            vhsr = st.number_input("VHSR Distance (m)", 0.0, 20000.0, 0.0, 10.0)
        with c3:
            ts = st.number_input("Top Speed (m/s)", 0.0, 13.0, 8.5, 0.1)
            acc25 = st.number_input("Accelerations >2.5 m/s^2", 0.0, 100.0, 12.0, 1.0)
            acc35 = st.number_input("Accelerations >3.5 m/s^2", 0.0, 100.0, 2.0, 1.0)
            max_acc = st.number_input("Max Accel (m/s^2)", 0.0, 10.0, 0.0, 0.1)
        c4, c5 = st.columns(2)
        with c4:
            strain = st.number_input("Player Load / Strain (optional)", 0.0, 5000.0, 0.0, 1.0)
            rpe = st.slider("RPE (1-10)", 1, 10, 6)
        with c5:
            notes = st.text_input("Notes", value="")
        gps_submit = st.form_submit_button("Add Session")
        if gps_submit:
            srpe = rpe * duration if duration and rpe else np.nan
            row = {
                "Date (YYYY-MM-DD)": str(d), "Session Name": session, "Duration (min)": duration,
                "Total Distance (m)": dist, "HSR Distance (m)": hsr, "VHSR Distance (m)": vhsr,
                "Top Speed (m/s)": ts, "Accelerations >2.5 m/s^2": acc25, "Accelerations >3.5 m/s^2": acc35,
                "Max Accel (m/s^2)": max_acc, "Player Load / Strain (optional)": strain,
                "RPE (1-10)": rpe, "sRPE (RPE*Duration)": srpe, "Notes": notes
            }
            gps = pd.concat([gps, pd.DataFrame([row])], ignore_index=True)
            st.success("Saved GPS session (not yet persisted — click 'Save All' in sidebar).")
    st.dataframe(gps)

with tab4:
    st.subheader("Gym Log")
    with st.form("gym_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            d = st.date_input("Date", value=date.today(), key="gym_date")
            lift = st.text_input("Lift", value="Back Squat")
        with c2:
            s = st.number_input("Set", 1, 20, 1, 1)
            reps = st.number_input("Reps", 1, 30, 3, 1)
        with c3:
            w = st.number_input("Weight (kg)", 0.0, 500.0, 180.0, 2.5)
            vel = st.number_input("Velocity (m/s, optional)", 0.0, 5.0, 0.0, 0.01)
            notes = st.text_input("Notes", value="")
        submit_gym = st.form_submit_button("Add Set")
        if submit_gym:
            one_rm = w * (1 + reps/30.0) if w and reps else np.nan
            row = {
                "Date (YYYY-MM-DD)": str(d), "Lift": lift, "Set": int(s),
                "Reps": int(reps), "Weight (kg)": w, "Estimated 1RM (kg)": one_rm if one_rm else np.nan,
                "Velocity (m/s, optional)": vel if vel>0 else np.nan, "Notes": notes
            }
            gym = pd.concat([gym, pd.DataFrame([row])], ignore_index=True)
            st.success("Saved gym set (not yet persisted — click 'Save All' in sidebar).")
    st.dataframe(gym)

with tab5:
    st.subheader("Body Composition")
    with st.form("body_form"):
        d = st.date_input("Date", value=date.today(), key="body_date")
        method = st.selectbox("Method", ["InBody","Caliper","Other"])
        bw = st.number_input("Weight (kg)", 0.0, 300.0, 120.0, 0.1)
        bf = st.number_input("Body Fat %", 0.0, 60.0, 24.0, 0.1)
        smm = st.number_input("SMM (kg)", 0.0, 100.0, 54.0, 0.1)
        vf = st.number_input("Visceral Fat (optional)", 0.0, 50.0, 0.0, 0.1)
        notes = st.text_input("Notes", value="")
        submit_body = st.form_submit_button("Add Body Comp")
        if submit_body:
            row = {"Date (YYYY-MM-DD)": str(d), "Method (InBody/Caliper)": method, "Weight (kg)": bw, "Body Fat %": bf,
                   "SMM (kg)": smm, "Visceral Fat (optional)": vf if vf>0 else np.nan, "Notes": notes}
            body = pd.concat([body, pd.DataFrame([row])], ignore_index=True)
            st.success("Saved body composition entry (not yet persisted — click 'Save All' in sidebar).")
    st.dataframe(body)

    st.markdown("---")
    st.subheader("Performance Tests")
    with st.form("tests_form"):
        d = st.date_input("Date", value=date.today(), key="tests_date")
        test = st.text_input("Test (Yo-Yo/MAS/30-15/3RM/CMJ etc.)", value="CMJ")
        score = st.text_input("Score/Time/Level", value="40 cm")
        notes = st.text_input("Notes", value="")
        submit_test = st.form_submit_button("Add Test")
        if submit_test:
            row = {"Date (YYYY-MM-DD)": str(d), "Test (Yo-Yo/MAS/30-15/3RM/CMJ etc.)": test, "Score/Time/Level": score, "Notes": notes}
            tests = pd.concat([tests, pd.DataFrame([row])], ignore_index=True)
            st.success("Saved test entry (not yet persisted — click 'Save All' in sidebar).")
    st.dataframe(tests)

with tab1:
    st.subheader("Dashboard — Trends")
    colA, colB = st.columns(2)
    with colA:
        st.markdown("**Weight Trend**")
        if len(wellness):
            wd = wellness.copy()
            wd["Date"] = pd.to_datetime(wd["Date (YYYY-MM-DD)"], errors="coerce")
            wd = wd.dropna(subset=["Date"]).sort_values("Date")
            fig = plt.figure(figsize=(7,4))
            plt.plot(wd["Date"], pd.to_numeric(wd["Body Weight (kg)"], errors="coerce"), marker="o")
            plt.title("Weight (kg)"); plt.xlabel("Date"); plt.ylabel("Weight (kg)"); plt.grid(True)
            st.pyplot(fig); plt.close(fig)
        else:
            st.info("No wellness data yet. Add data in the Wellness tab.")
    with colB:
        st.markdown("**GPS Performance**")
        if len(gps):
            gd = gps.copy()
            gd["Date"] = pd.to_datetime(gd["Date (YYYY-MM-DD)"], errors="coerce")
            gd = gd.dropna(subset=["Date"]).sort_values("Date")
            by_day = gd.groupby("Date").agg({"Top Speed (m/s)": "max", "Total Distance (m)": "sum"}).reset_index()
            fig2 = plt.figure(figsize=(7,4))
            plt.plot(by_day["Date"], pd.to_numeric(by_day["Top Speed (m/s)"], errors="coerce"), marker="o", label="Top Speed (m/s)")
            plt.plot(by_day["Date"], pd.to_numeric(by_day["Total Distance (m)"], errors="coerce"), marker="s", label="Distance (m)")
            plt.title("Top Speed & Distance"); plt.xlabel("Date"); plt.ylabel("Value"); plt.grid(True); plt.legend()
            st.pyplot(fig2); plt.close(fig2)
        else:
            st.info("No GPS data yet. Add data in the GPS tab.")

    st.markdown("---")
    st.markdown("**Gym Strength Progress**")
    if len(gym):
        gymd = gym.copy()
        gymd["Date"] = pd.to_datetime(gymd["Date (YYYY-MM-DD)"], errors="coerce")
        gymd = gymd.dropna(subset=["Date"]).sort_values("Date")
        lifts_focus = gymd[gymd["Lift"].str.lower().str.contains("squat|bench", na=False)]
        by_day2 = lifts_focus.groupby(["Date","Lift"]).agg({"Weight (kg)":"max"}).reset_index()
        for lift in by_day2["Lift"].unique():
            sub = by_day2[by_day2["Lift"]==lift]
            fig3 = plt.figure(figsize=(7,4))
            plt.plot(sub["Date"], pd.to_numeric(sub["Weight (kg)"], errors="coerce"), marker="o")
            plt.title(f"{lift} — Best Set Weight"); plt.xlabel("Date"); plt.ylabel("Weight (kg)"); plt.grid(True)
            st.pyplot(fig3); plt.close(fig3)
    else:
        st.info("No gym data yet. Add data in the Gym tab.")

with tab6:
    st.subheader("AI-style Daily Summary")
    today = date.today()
    res = ai_daily_summary(today, wellness, gps, gym)

    st.markdown("**Summary**")
    st.code(res["summary"] or "No data entered for today yet.")

    st.markdown("**Insights**")
    if res["insights"]:
        for i in res["insights"]:
            st.write(f"- {i}")
    else:
        st.write("- Enter data to see insights.")

    st.markdown("**Recovery Plan (next 24h)**")
    for r in res["recovery"]:
        st.write(f"- {r}")

    if res["red_flags"]:
        st.error("Red Flags:\n- " + "\n- ".join(res["red_flags"]))
