# Updated Streamlit App with OpenAI Chat Assistant and Portfolio Tabs
import streamlit as st
import pandas as pd
import openai
import yfinance as yf
from datetime import datetime
import os


# --- Configuration ---
openai.api_key = os.getenv("OPENAI_API_KEY")  # You can set this securely in Streamlit Cloud or your local .env


st.set_page_config(page_title="AI Portfolio Chat", layout="wide")
st.title("💬 AI Stock Assistant with Portfolio Integration")


# --- Session State Initialization ---
if "chats" not in st.session_state:
    st.session_state.chats = {}


if "risk" not in st.session_state:
    st.session_state.risk = "moderate"
    st.session_state.tax = "moderate"
    st.session_state.horizon = "medium"


# --- Sidebar for Preferences ---
st.sidebar.header("Investor Profile")
st.session_state.risk = st.sidebar.selectbox("Risk Tolerance", ["conservative", "moderate", "aggressive"], index=1)
st.session_state.tax = st.sidebar.selectbox("Tax Sensitivity", ["low", "moderate", "high"], index=1)
st.session_state.horizon = st.sidebar.selectbox("Investment Horizon", ["short", "medium", "long"], index=1)


# --- Load CSV Portfolio ---
st.sidebar.header("Upload Additional Portfolios")
csv_upload = st.sidebar.file_uploader("Upload CSV Portfolio", type=["csv"])
portfolios = {}


if csv_upload:
    df = pd.read_csv(csv_upload)
    portfolios["Uploaded CSV"] = df


# --- Load Interactive Brokers PDF Portfolio ---
ib_data = {
    'Symbol': ['AAPL', 'AMT', 'BMY', 'BYND', 'GOOG', 'MA', 'NVDA', 'PANW', 'PFE', 'SPY', 'TGT', 'TSLA', 'VOO', 'VTRS', 'USNQX'],
    'Quantity': [700, 250, 500, 1, 2300, 200, 6000, 528, 850, 300, 350, 215, 200, 124, 1153.805],
    'Cost': [144.39, 215.66, 64.63, 120.06, 94.44, 292.10, 13.52, 148.51, 35.70, 482.55, 173.80, 297.17, 372.32, 15.78, 32.27],
    'Current': [218.27, 216.23, 61.07, 3.55, 166.25, 535.69, 117.70, 182.32, 26.28, 563.98, 104.06, 248.71, 520.26, 9.15, 48.63],
}
ib_df = pd.DataFrame(ib_data)
portfolios["Interactive Brokers Trust"] = ib_df


# --- Tabs per Portfolio ---
tabs = st.tabs(list(portfolios.keys()) + ["Assistant"])


# --- Portfolio Tabs ---
for i, (name, df) in enumerate(portfolios.items()):
    with tabs[i]:
        st.header(f"📊 Portfolio: {name}")
        df["Value"] = df["Quantity"] * df["Current"]
        df["Gain/Loss"] = (df["Current"] - df["Cost"]) * df["Quantity"]
        st.dataframe(df)
        total = df["Value"].sum()
        st.metric("Total Value", f"${total:,.2f}")


# --- Chat Assistant Tab ---
with tabs[-1]:
    st.header("🤖 Ask Me Anything - Chat Assistant")
    portfolio_text = ""
    for name, df in portfolios.items():
        portfolio_text += f"\n{name} Portfolio:\n{df.to_string(index=False)}"


    if name not in st.session_state.chats:
        st.session_state.chats[name] = []


    for msg in st.session_state.chats[name]:
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])


    if prompt := st.chat_input("Ask anything: market, taxes, advice..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.chats[name].append({"role": "user", "content": prompt})


        # Send to OpenAI
        system_prompt = f"You are a financial advisor assistant. Use the investor profile below and portfolio data to answer.\n\nRisk: {st.session_state.risk}\nTax Sensitivity: {st.session_state.tax}\nHorizon: {st.session_state.horizon}\n\nUser Portfolio Data:\n{portfolio_text}"


        messages = [{"role": "system", "content": system_prompt}] + st.session_state.chats[name]


        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.3
            )
            reply = response.choices[0].message.content
        except Exception as e:
            reply = f"⚠️ Error from OpenAI: {str(e)}"


        st.chat_message("assistant").markdown(reply)
        st.session_state.chats[name].append({"role": "assistant", "content": reply})


st.caption("Built with ❤️ using Streamlit and OpenAI")