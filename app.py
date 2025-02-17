import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import timedelta

# Judul aplikasi
st.title("Perbandingan Saham dengan Metode Persentase dan VaR")

# Load dataset
final_df = pd.read_csv('final_df.csv', delimiter=',')
comparison_table = pd.DataFrame(final_df)

# Input kode saham
st.sidebar.header("Input Saham Target")
target_stock = st.sidebar.text_input("Kode Saham Target", value="ARCI.JK")

# Ambil data saham target dari final_df
if target_stock in final_df['Kode'].values:
    stock_data = final_df[final_df['Kode'] == target_stock].iloc[0]
    target_roa = stock_data['RoA']
    target_mc = stock_data['Market Cap']
    target_roe = stock_data['RoE']
    target_subsektor = stock_data['Sub Sektor']
else:
    st.error("Kode saham tidak ditemukan dalam dataset.")
    st.stop()

# Fungsi untuk menghitung persentase perbedaan
def calculate_percentage(filtered_table):
    data = []
    for index, row in filtered_table.iterrows():
        differences = {
            'Kode': row['Kode'],
            'RoA_Percentage': abs(row['RoA'] - target_roa) / abs(target_roa) * 100,
            'Market_Cap_Percentage': abs(row['Market Cap'] - target_mc) / abs(target_mc) * 100,
            'RoE_Percentage': abs(row['RoE'] - target_roe) / abs(target_roe) * 100,
        }
        differences['Total_Percentage'] = sum(differences.values()) - differences['Kode']
        data.append(differences)
    
    df = pd.DataFrame(data).sort_values(by='Total_Percentage')
    return df.head(3)

# Fungsi untuk membandingkan dalam subsektor
def compare_with_subsektor():
    filtered_table = comparison_table[(comparison_table['Sub Sektor'] == target_subsektor) &
                                      (comparison_table['Kode'] != target_stock)]
    if filtered_table.empty:
        st.warning(f"Tidak ada saham lain dalam subsektor {target_subsektor} untuk dibandingkan.")
        return pd.DataFrame()
    return calculate_percentage(filtered_table)

# Fungsi untuk membandingkan tanpa subsektor
def compare_without_subsektor():
    filtered_table = comparison_table[comparison_table['Kode'] != target_stock]
    return calculate_percentage(filtered_table)

# Jalankan perbandingan
df_with_subsektor = compare_with_subsektor()
df_without_subsektor = compare_without_subsektor()

st.subheader("Perbandingan Saham dalam Subsektor yang Sama")
st.dataframe(df_with_subsektor)

st.subheader("Perbandingan Saham Tanpa Mempertimbangkan Subsektor")
st.dataframe(df_without_subsektor)

# Perhitungan VaR
st.header("Perhitungan Value at Risk (VaR)")

def calculate_var(stock_code):
    stock_date = pd.to_datetime(final_df[final_df['Kode'] == stock_code]['Date'].iloc[0])
    data = yf.download(stock_code, start=stock_date, end=stock_date + timedelta(days=365), interval='1wk')['Close']
    daily_returns = data.pct_change().dropna()
    return np.percentile(daily_returns, 1), np.percentile(daily_returns, 99)

var_data = []
for stock in [target_stock] + df_with_subsektor['Kode'].tolist():
    try:
        var_1, var_99 = calculate_var(stock)
        var_data.append({'Kode': stock, 'VaR 1%': var_1, 'VaR 99%': var_99})
    except:
        st.warning(f"Data tidak tersedia untuk {stock}")

var_df = pd.DataFrame(var_data)
st.dataframe(var_df)
