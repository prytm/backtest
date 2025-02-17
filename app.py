import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# Load dataset
@st.cache_data
def load_data():
    return pd.read_csv('final_df.csv')

final_df = load_data()

# Streamlit UI
st.title("Analisis Perbandingan Saham dengan Persentase & VaR")

# Input kode saham (hanya ini yang perlu dimasukkan)
st.sidebar.header("Input Saham Target")
target_stock = st.sidebar.text_input("Kode Saham Target", value="ARCI.JK")

# Ambil data target secara otomatis
if target_stock in final_df['Kode'].values:
    target_data = final_df[final_df['Kode'] == target_stock].iloc[0]
    target_roa = target_data['RoA']
    target_mc = target_data['Market Cap']
    target_roe = target_data['RoE']
    target_subsektor = target_data['Sub Sektor']
    target_date = pd.to_datetime(target_data['Date'])
else:
    st.error("Kode saham tidak ditemukan dalam dataset!")
    st.stop()

# Fungsi untuk menghitung persentase perbedaan
def calculate_percentage(filtered_table):
    total_percentage = {}
    percentage_details = {}

    for metric, target_value in zip(['RoA', 'Market Cap', 'RoE'], [target_roa, target_mc, target_roe]):
        filtered_table[metric] = pd.to_numeric(filtered_table[metric], errors='coerce')  # Pastikan numeric
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

# Perbandingan dalam subsektor
def compare_with_subsektor():
    filtered_table = final_df[(final_df['Sub Sektor'] == target_subsektor) & (final_df['Kode'] != target_stock)]
    if filtered_table.empty:
        st.warning(f"Tidak ada saham lain dalam subsektor {target_subsektor} untuk dibandingkan.")
        return [], {}

    return calculate_percentage(filtered_table)

# Perbandingan tanpa subsektor
def compare_without_subsektor():
    filtered_table = final_df[final_df['Kode'] != target_stock]
    return calculate_percentage(filtered_table)

# Jalankan perbandingan
min_stocks_with_subsektor, details_with_subsektor = compare_with_subsektor()
min_stocks_without_subsektor, details_without_subsektor = compare_without_subsektor()

# Tampilkan hasil dalam DataFrame
def create_result_df(sorted_stocks, details):
    data = []
    for stock, _ in sorted_stocks:
        row = {
            'Kode': stock,
            'RoA Diff (%)': f"{details[stock]['RoA']:.2f}%" if 'RoA' in details[stock] else "-",
            'Market Cap Diff (%)': f"{details[stock]['Market Cap']:.2f}%" if 'Market Cap' in details[stock] else "-",
            'RoE Diff (%)': f"{details[stock]['RoE']:.2f}%" if 'RoE' in details[stock] else "-",
        }
        data.append(row)
    return pd.DataFrame(data)

st.subheader("📊 Perbandingan Saham dalam Subsektor")
if min_stocks_with_subsektor:
    st.dataframe(create_result_df(min_stocks_with_subsektor, details_with_subsektor))
else:
    st.write("Tidak ada saham untuk dibandingkan dalam subsektor yang sama.")

st.subheader("📊 Perbandingan Saham di Luar Subsektor")
st.dataframe(create_result_df(min_stocks_without_subsektor, details_without_subsektor))

# === Perhitungan Value at Risk (VaR) ===
st.header("📉 Perhitungan Value at Risk (VaR)")

# Fungsi untuk menghitung VaR
def calculate_var(stock_code, start_date):
    try:
        data = yf.download(stock_code, start=start_date, end=start_date + timedelta(days=365), interval='1wk')['Close']
        daily_returns = data.pct_change().dropna()
        var_1 = np.percentile(daily_returns, 1)
        var_99 = np.percentile(daily_returns, 99)
        return var_1, var_99
    except Exception as e:
        st.error(f"Gagal menghitung VaR untuk {stock_code}: {e}")
        return None, None

# Hitung VaR untuk saham target
var_target_1, var_target_99 = calculate_var(target_stock, target_date)

# Tampilkan hasil dalam DataFrame
var_results = [{'Kode': target_stock, 'VaR 1%': f"{var_target_1:.4f}" if var_target_1 is not None else "-",
                'VaR 99%': f"{var_target_99:.4f}" if var_target_99 is not None else "-"}]

# Hitung VaR untuk saham terdekat dalam subsektor
if min_stocks_with_subsektor:
    closest_stock = min_stocks_with_subsektor[0][0]
    closest_date = pd.to_datetime(final_df[final_df['Kode'] == closest_stock]['Date'].iloc[0])
    var_closest_1, var_closest_99 = calculate_var(closest_stock, closest_date)

    var_results.append({'Kode': closest_stock, 'VaR 1%': f"{var_closest_1:.4f}" if var_closest_1 is not None else "-",
                        'VaR 99%': f"{var_closest_99:.4f}" if var_closest_99 is not None else "-"})

st.dataframe(pd.DataFrame(var_results))
