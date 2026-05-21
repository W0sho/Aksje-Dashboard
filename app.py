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

# Ordbok for fundamentale nøkkeltall (Yfinance-nøkkel : Visningsnavn)
FUNDAMENTALE_METRIKKER = {
    "trailingPE": "P/E (Trailing)",
    "forwardPE": "P/E (Forward)",
    "priceToSalesTrailing12Months": "P/S (Price/Sales)",
    "priceToBook": "P/B (Price/Book)",
    "dividendYield": "Utbyttegrad (Yield %)",
    "profitMargins": "Profit Margin (%)",
    "marketCap": "Markedsverdi (Market Cap)"
}

# --- SIDEBAR: INNSTILLINGER ---
st.sidebar.header("1. Velg Periode")
period = st.sidebar.selectbox("Tidsperiode for graf:", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)

# Gitter for aksjevalg
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

# Gitter for fundamentale nøkkeltall
st.sidebar.header("3. Fundamentale Nøkkeltall")
with st.sidebar.expander("Velg nøkkeltall for tabell", expanded=True):
    valgte_metrikker = []
    # Setter P/E og Market Cap som standard
    for kilde_navn, visnings_navn in FUNDAMENTALE_METRIKKER.items():
        default_metrikk = True if kilde_navn in ["trailingPE", "marketCap"] else False
        if st.checkbox(visnings_navn, value=default_metrikk, key=f"met_{kilde_navn}"):
            valgte_metrikker.append(kilde_navn)


# --- HOVEDSKJERM: DATABEHANDLING OG VISNING ---
if valgte_tickers:
    try:
        # 1. Hent og vis historisk kursevolusjon (Graf)
        data = yf.download(valgte_tickers, period=period, group_by='ticker')
        
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

        
        # 2. Hent fundamentale nøkkeltall via yf.Ticker (Tabell)
        st.subheader("📊 Fundamental Sammenligning")
        
        with st.spinner("Henter fundamentale nøkkeltall fra API..."):
            tabell_data = []
            
            for t in valgte_tickers:
                ticker_info = yf.Ticker(t).info
                rad = {"Selskap": TOPP_30_AKSJER.get(t, t), "Ticker": t}
                
                for metrikk in valgte_metrikker:
                    verdi = ticker_info.get(metrikk, None)
                    
                    # VIKTIG: Vi lagrer råtallet (milliarder for market cap) uten å gjøre det om til tekst
                    if verdi is not None:
                        if metrikk == "marketCap":
                            rad[FUNDAMENTALE_METRIKKER[metrikk]] = verdi / 1e9  # Lagre som tall i milliarder
                        else:
                            rad[FUNDAMENTALE_METRIKKER[metrikk]] = verdi
                    else:
                        rad[FUNDAMENTALE_METRIKKER[metrikk]] = None
                        
                tabell_data.append(rad)
            
            # Lag dataframe
            df_fundamental = pd.DataFrame(tabell_data).set_index("Selskap")
            
            # 3. VIKTIG: Vi bruker Streamlit sin innebygde .style for å vise tallene pent, 
            # uten å ødelegge for sorteringen!
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