import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import timedelta

# Load dataset
final_df = pd.read_csv('final_df.csv', delimiter=',')
comparison_table = pd.DataFrame(final_df)

# Judul aplikasi
st.title("Perbandingan Saham dengan Metode Persentase dan VaR")

# Input nama saham saja
st.sidebar.header("Input Saham Target")
target_stock = st.sidebar.text_input("Kode Saham Target", value="ARCI.JK")

# Ambil otomatis data saham target dari final_df
if target_stock in final_df['Kode'].values:
    stock_data = final_df[final_df['Kode'] == target_stock].iloc[0]
    target_roa = stock_data['RoA']
    target_mc = stock_data['Market Cap']
    target_roe = stock_data['RoE']
    target_subsektor = stock_data['Sub Sektor']
else:
    st.error("Kode saham tidak ditemukan di dataset.")
    st.stop()

# Fungsi untuk menghitung persentase perbedaan
def calculate_percentage(filtered_table):
    total_percentage = {}
    percentage_details = {}

    for metric, target_value in zip(['RoA', 'Market Cap', 'RoE'], [target_roa, target_mc, target_roe]):
        differences = abs(filtered_table[metric] - target_value)
        percentage = (differences / abs(target_value)) * 100
        filtered_table[f'{metric}_Percentage'] = percentage

        for stock, percent in zip(filtered_table['Kode'], percentage):
            if stock not in total_percentage:
                total_percentage[stock] = 0
                percentage_details[stock] = {}
            total_percentage[stock] += percent
            percentage_details[stock][metric] = percent

    sorted_total = sorted(total_percentage.items(), key=lambda x: abs(x[1]))[:3]
    return sorted_total, percentage_details

# Fungsi untuk membandingkan dengan subsektor yang sama
def compare_with_subsektor():
    filtered_table = comparison_table[(comparison_table['Sub Sektor'] == target_subsektor) &
                                      (comparison_table['Kode'] != target_stock)]
    if filtered_table.empty:
        st.warning(f"Tidak ada saham lain dalam subsektor {target_subsektor} untuk dibandingkan.")
        return [], {}
    return calculate_percentage(filtered_table)

# Fungsi untuk membandingkan tanpa subsektor
def compare_without_subsektor():
    filtered_table = comparison_table[comparison_table['Kode'] != target_stock]
    return calculate_percentage(filtered_table)

# Jalankan perbandingan
min_stocks_with_subsektor, details_with_subsektor = compare_with_subsektor()
min_stocks_without_subsektor, details_without_subsektor = compare_without_subsektor()

# Hitung dan tampilkan VaR
st.header("Perhitungan Value at Risk (VaR)")

if min_stocks_with_subsektor:
    subsektor_stock = min_stocks_with_subsektor[0][0]
    target_date_subsektor = pd.to_datetime(final_df[final_df['Kode'] == subsektor_stock]['Date'].iloc[0])
    
    data_1 = yf.download(subsektor_stock, start=target_date_subsektor, end=target_date_subsektor + timedelta(days=365), interval='1wk')['Close']
    daily_returns_1 = data_1.pct_change().dropna()

    var_subsektor_1 = np.percentile(daily_returns_1, 1)
    var_subsektor_99 = np.percentile(daily_returns_1, 99)

    st.write(f"**{subsektor_stock}**")
    st.write(f"- VaR 1%: {var_subsektor_1:.4f}")
    st.write(f"- VaR 99%: {var_subsektor_99:.4f}")

# Download data untuk saham target
target_date = pd.to_datetime(stock_data['Date'])
data = yf.download(target_stock, start=target_date, end=target_date + timedelta(days=365), interval='1wk')['Close']
daily_returns = data.pct_change().dropna()

var_target_1 = np.percentile(daily_returns, 1)
var_target_99 = np.percentile(daily_returns, 99)

st.write(f"**{target_stock}**")
st.write(f"- VaR 1%: {var_target_1:.4f}")
st.write(f"- VaR 99%: {var_target_99:.4f}")
