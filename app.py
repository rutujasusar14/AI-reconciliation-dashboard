import pandas as pd
import streamlit as st

st.set_page_config(page_title="AI Reconciliation System", layout="wide")

# ------------------ HEADER ------------------
st.title("💰 AI-Powered Transaction Reconciliation")
st.caption("Detect, classify & explain mismatches intelligently")

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_csv("data.csv")

# ------------------ PREPROCESS ------------------
df['date'] = pd.to_datetime(df['date'])

company = df[df['type'] == 'company']
bank = df[df['type'] == 'bank']

# ------------------ SMART MATCH FUNCTION ------------------
def match_transactions(comp, bank):
    results = []

    for _, c in comp.iterrows():
        match = bank[(bank['amount'] == c['amount'])]

        if match.empty:
            results.append({
                "amount": c['amount'],
                "issue": "Missing in Bank",
                "confidence": 0.0
            })
        else:
            b = match.iloc[0]
            days_diff = abs((c['date'] - b['date']).days)

            if days_diff == 0:
                issue = "Perfect Match"
                confidence = 1.0
            elif days_diff <= 2:
                issue = "Settlement Delay"
                confidence = 0.8
            else:
                issue = "Date Mismatch"
                confidence = 0.5

            results.append({
                "amount": c['amount'],
                "issue": issue,
                "confidence": confidence
            })

    return pd.DataFrame(results)

result_df = match_transactions(company, bank)

# ------------------ EXTRA IN BANK ------------------
extra_bank = bank[~bank['amount'].isin(company['amount'])]

extra_rows = []
for _, row in extra_bank.iterrows():
    extra_rows.append({
        "amount": row['amount'],
        "issue": "Unexpected Bank Entry",
        "confidence": 0.3
    })

extra_df = pd.DataFrame(extra_rows)

# ------------------ DUPLICATES ------------------
duplicates = df[df.duplicated(subset=['amount', 'date'], keep=False)]
dup_rows = []

for _, row in duplicates.iterrows():
    dup_rows.append({
        "amount": row['amount'],
        "issue": "Duplicate Transaction",
        "confidence": 0.4
    })

dup_df = pd.DataFrame(dup_rows)

# ------------------ FINAL DATA ------------------
final_df = pd.concat([result_df, extra_df, dup_df])

# ------------------ METRICS ------------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Transactions", len(df))
col2.metric("Issues Found", len(final_df[final_df['issue'] != "Perfect Match"]))
col3.metric("Perfect Matches", len(final_df[final_df['issue'] == "Perfect Match"]))

st.markdown("---")

# ------------------ FILTER ------------------
issue_filter = st.selectbox("Filter by Issue", ["All"] + list(final_df['issue'].unique()))

if issue_filter != "All":
    display_df = final_df[final_df['issue'] == issue_filter]
else:
    display_df = final_df

# ------------------ DISPLAY ------------------
st.subheader("🔍 Analysis Result")
st.dataframe(display_df, use_container_width=True)

# ------------------ AI EXPLANATION ------------------
st.subheader("🤖 AI Explanation")

for _, row in display_df.iterrows():
    if row['issue'] == "Missing in Bank":
        st.error(f"₹{row['amount']} not found in bank → Possible system failure or pending settlement.")
    elif row['issue'] == "Settlement Delay":
        st.warning(f"₹{row['amount']} delayed → Normal banking delay (1–2 days).")
    elif row['issue'] == "Date Mismatch":
        st.info(f"₹{row['amount']} mismatch → Needs manual verification.")
    elif row['issue'] == "Unexpected Bank Entry":
        st.warning(f"₹{row['amount']} unknown entry → Could be refund or fraud.")
    elif row['issue'] == "Duplicate Transaction":
        st.error(f"₹{row['amount']} duplicate → Possible double processing.")

st.markdown("---")

# ------------------ RAW DATA ------------------
st.subheader("📄 Raw Data")
st.dataframe(df, use_container_width=True)