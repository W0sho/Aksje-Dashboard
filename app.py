import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Sett opp sidetittel og layout
st.set_page_config(page_title="Fundamentalt Aksjedashbord", layout="wide")
st.title("📈 Aksjedashbord med Fundamental Analyse")
st.write("Velg aksjer og kryss av for de fundamentale nøkkeltallene du ønsker å sammenligne.")

# Ordbok med Topp 30 selskaper
TOPP_30_AKSJER = {
    "NVDA": "NVIDIA", "GOOGL": "Alphabet (Google)", "AAPL": "Apple", 
    "MSFT": "Microsoft", "AMZN": "Amazon", "TSM": "TSMC", 
    "AVGO": "Broadcom", "TSLA": "Tesla", "META": "Meta Platforms", 
    "WMT": "Walmart", "BRK-B": "Berkshire Hathaway", "LLY": "Eli Lilly", 
    "JPM": "JPMorgan Chase", "AMD": "AMD", "XOM": "Exxon Mobil", 
    "V": "Visa", "ASML": "ASML", "ORCL": "Oracle", "COST": "Costco", 
    "NFLX": "Netflix", "KO": "Coca-Cola"
}

# Ordbok for fundamentale nøkkeltall
FUNDAMENTALE_METRIKKER = {
    "trailingPE": "P/E (Trailing)",
    "forwardPE": "P/E (Forward)",
    "priceToSalesTrailing12Months": "P/S (Price/Sales)",
    "priceToBook": "P/B (Price/Book)",
    "dividendYield": "Utbyttegrad (Yield %)",
    "profitMargins": "Profit Margin (%)",
    "marketCap": "Markedsverdi (Market Cap)"
}

# --- CACHING FUNKSJONER (Løser "Too Many Requests") ---
# ttl=900 betyr at dataene lagres i 15 minutter før de hentes på nytt

@st.cache_data(ttl=900)
def hent_historisk_data(tickers, period):
    return yf.download(tickers, period=period, group_by='ticker')

@st.cache_data(ttl=900)
def hent_ticker_info(ticker):
    return yf.Ticker(ticker).info


# --- SIDEBAR: INNSTILLINGER ---
st.sidebar.header("1. Velg Periode")
period = st.sidebar.selectbox("Tidsperiode for graf:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

st.sidebar.header("2. Velg Aksjer")
with st.sidebar.expander("Åpne aksjeliste", expanded=True):
    valgte_tickers = []
    col1, col2 = st.columns(2)
    for i, (ticker, navn) in enumerate(TOPP_30_AKSJER.items()):
        default_valg = True if ticker in ["NVDA", "AAPL"] else False
        if i % 2 == 0:
            with col1:
                if st.checkbox(f"{ticker}", value=default_valg, key=f"tk_{ticker}"):
                    valgte_tickers.append(ticker)
        else:
            with col2:
                if st.checkbox(f"{ticker}", value=default_valg, key=f"tk_{ticker}"):
                    valgte_tickers.append(ticker)

st.sidebar.header("3. Fundamentale Nøkkeltall")
with st.sidebar.expander("Velg nøkkeltall for tabell", expanded=True):
    valgte_metrikker = []
    for kilde_navn, visnings_navn in FUNDAMENTALE_METRIKKER.items():
        default_metrikk = True if kilde_navn in ["trailingPE", "marketCap"] else False
        if st.checkbox(visnings_navn, value=default_metrikk, key=f"met_{kilde_navn}"):
            valgte_metrikker.append(kilde_navn)


# --- HOVEDSKJERM: DATABEHANDLING OG VISNING ---
if valgte_tickers:
    try:
        # Bruker den cachede funksjonen i stedet for yf.download direkte
        data = hent_historisk_data(valgte_tickers, period)
        
        fig = go.Figure()
        if len(valgte_tickers) == 1:
            t = valgte_tickers[0]
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            fig.add_trace(go.Scatter(x=data.index, y=data['Close'], name=f'{t} Sluttkurs'))
        else:
            for t in valgte_tickers:
                if t in data.columns.levels[0]:
                    fig.add_trace(go.Scatter(x=data[t].index, y=data[t]['Close'], name=TOPP_30_AKSJER.get(t, t)))

        fig.update_layout(title="Kursutvikling", yaxis_title="Pris (USD)", template="plotly_dark", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📊 Fundamental Sammenligning")
        
        with st.spinner("Henter fundamentale nøkkeltall..."):
            tabell_data = []
            
            for t in valgte_tickers:
                # Bruker den cachede funksjonen her også!
                ticker_info = hent_ticker_info(t)
                rad = {"Selskap": TOPP_30_AKSJER.get(t, t), "Ticker": t}
                
                for metrikk in valgte_metrikker:
                    verdi = ticker_info.get(metrikk, None)
                    
                    if verdi is not None:
                        if metrikk == "marketCap":
                            rad[FUNDAMENTALE_METRIKKER[metrikk]] = verdi / 1e9
                        else:
                            rad[FUNDAMENTALE_METRIKKER[metrikk]] = verdi
                    else:
                        rad[FUNDAMENTALE_METRIKKER[metrikk]] = None
                        
                tabell_data.append(rad)
            
            df_fundamental = pd.DataFrame(tabell_data).set_index("Selskap")
            
            st.dataframe(
                df_fundamental.style.format({
                    "P/E (Trailing)": "{:.2f}",
                    "P/E (Forward)": "{:.2f}",
                    "P/S (Price/Sales)": "{:.2f}",
                    "P/B (Price/Book)": "{:.2f}",
                    "Utbyttegrad (Yield %)": "{:.2%}",
                    "Profit Margin (%)": "{:.2%}",
                    "Markedsverdi (Market Cap)": "${:.1f} Mrd"
                }, na_rep="N/A"),
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Det oppstod en feil under henting av data: {e}")
else:
    st.info("Kryss av for minst én aksje i sidebaren for å starte.")
