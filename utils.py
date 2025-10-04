
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def readiness_score(sleep_hours=None, stress=None, soreness=None, mood=None, sRPE_today=None, sRPE_avg7=None):
    score = 80.0
    if sleep_hours is not None:
        if sleep_hours >= 8: score += 5
        elif sleep_hours < 6.5: score -= 8
        elif sleep_hours < 7: score -= 4
    for val, neg in [(stress, True),(soreness, True),(mood, False)]:
        if val is None: continue
        try:
            v = float(val)
            if neg:
                if v >= 4: score -= 6
                elif v >= 3: score -= 3
            else:
                if v >= 4: score += 3
                elif v <= 2: score -= 4
        except: pass
    if sRPE_today is not None and sRPE_avg7 not in (None, 0, np.nan):
        try:
            delta = (sRPE_today - sRPE_avg7) / sRPE_avg7
            if delta > 0.3: score -= 8
            elif delta > 0.15: score -= 4
            elif delta < -0.3: score += 3
        except: pass
    return max(0, min(100, round(score, 1)))

def ai_daily_summary(today, wellness_df, gps_df, gym_df):
    def within_7(df):
        try:
            d = pd.to_datetime(df["Date (YYYY-MM-DD)"], errors="coerce").dt.date
            mask = (d <= today) & (d >= (today - timedelta(days=6)))
            return df[mask]
        except Exception:
            return df.iloc[0:0]

    w_today = wellness_df[wellness_df["Date (YYYY-MM-DD)"] == str(today)]
    g_today = gps_df[gps_df["Date (YYYY-MM-DD)"] == str(today)]
    gym_today = gym_df[gym_df["Date (YYYY-MM-DD)"] == str(today)]

    w7 = within_7(wellness_df)
    g7 = within_7(gps_df)

    weight = pd.to_numeric(w_today.get("Body Weight (kg)", pd.Series([np.nan])), errors="coerce").dropna()
    weight = weight.iloc[-1] if len(weight) else None
    sleep_hours = pd.to_numeric(w_today.get("Sleep Hours", pd.Series([np.nan])), errors="coerce").dropna()
    sleep_hours = sleep_hours.iloc[-1] if len(sleep_hours) else None
    stress = pd.to_numeric(w_today.get("Stress (1-5)", pd.Series([np.nan])), errors="coerce").dropna()
    stress = stress.iloc[-1] if len(stress) else None
    soreness = pd.to_numeric(w_today.get("Soreness (1-5)", pd.Series([np.nan])), errors="coerce").dropna()
    soreness = soreness.iloc[-1] if len(soreness) else None
    mood = pd.to_numeric(w_today.get("Mood (1-5)", pd.Series([np.nan])), errors="coerce").dropna()
    mood = mood.iloc[-1] if len(mood) else None

    dist_today = pd.to_numeric(g_today.get("Total Distance (m)", pd.Series([0])), errors="coerce").sum() if len(g_today) else None
    top_speed_today = pd.to_numeric(g_today.get("Top Speed (m/s)", pd.Series([np.nan])), errors="coerce").max() if len(g_today) else None
    sRPE_today = pd.to_numeric(g_today.get("sRPE (RPE*Duration)", pd.Series([np.nan])), errors="coerce").sum() if len(g_today) else None

    weight_avg7 = pd.to_numeric(w7.get("Body Weight (kg)", pd.Series([np.nan])), errors="coerce").mean() if len(w7) else None
    top_speed_avg7 = pd.to_numeric(g7.get("Top Speed (m/s)", pd.Series([np.nan])), errors="coerce").mean() if len(g7) else None
    sRPE_avg7 = pd.to_numeric(g7.get("sRPE (RPE*Duration)", pd.Series([np.nan])), errors="coerce").mean() if len(g7) else None

    rscore = readiness_score(sleep_hours=sleep_hours, stress=stress, soreness=soreness, mood=mood,
                             sRPE_today=sRPE_today, sRPE_avg7=sRPE_avg7)

    insights = []
    if top_speed_today and top_speed_avg7:
        pct = 100*(top_speed_today - top_speed_avg7)/top_speed_avg7
        if pct >= 0:
            insights.append(f"Top speed {top_speed_today:.2f} m/s is {pct:.1f}% above 7-day avg.")
        else:
            insights.append(f"Top speed {top_speed_today:.2f} m/s is {abs(pct):.1f}% below 7-day avg.")
    if sRPE_today and sRPE_avg7 and sRPE_avg7 > 0:
        spike = (sRPE_today - sRPE_avg7)/sRPE_avg7
        if spike > 0.3:
            insights.append(f"Load spike +{spike*100:.0f}% vs 7-day avg — monitor recovery.")
        elif spike < -0.3:
            insights.append("Deload vs 7-day avg — good moment for technique/speed.")

    recovery = [
        "10–12 min easy bike flush",
        "8–10 min hips/ankles mobility",
        "Protein 30–40 g within 30 min post",
        "Hydration 1.5–2 L; electrolytes on heavy sweat days",
        "Optional: 5–8 min cold or contrast shower",
    ]

    red_flags = []
    if weight and weight_avg7 and weight_avg7 > 0:
        if (weight_avg7 - weight)/weight_avg7 > 0.01:
            red_flags.append("Weight drop >1% vs weekly avg")
    if sRPE_today and sRPE_avg7 and sRPE_avg7 > 0:
        if (sRPE_today - sRPE_avg7)/sRPE_avg7 > 0.3:
            red_flags.append("sRPE spike >30% vs weekly avg")

    load_label = "low"
    if sRPE_today is not None:
        if sRPE_avg7 and sRPE_avg7 > 0:
            ratio = sRPE_today / sRPE_avg7
            if ratio >= 1.2: load_label = "high"
            elif ratio >= 0.8: load_label = "medium"
        else:
            load_label = "medium"

    summary_lines = [
        f"READINESS: {rscore}/100",
        f"LOAD: {load_label}. Distance {dist_today if dist_today is not None else 0:.0f} m; Top speed {top_speed_today if top_speed_today else 0:.2f} m/s; sRPE {sRPE_today if sRPE_today else 0:.0f}.",
        f"Weight vs 7-day avg: {('%.1f kg vs %.1f kg' % (weight, weight_avg7)) if (weight and weight_avg7) else 'n/a'}."
    ]

    return {
        "summary": "\n".join(summary_lines),
        "insights": insights[:3],
        "recovery": recovery,
        "red_flags": red_flags
    }
