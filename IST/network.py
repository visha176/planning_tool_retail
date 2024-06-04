import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

def create_sample_file():
    # Creating a sample DataFrame with the required headers
    sample_data = {
        'DESIGN': ['Design1', 'Design2'],
        'STORE_NAME': ['Store1', 'Store2'],
        '1st Rcv Date': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'Shop Rcv Qty': [100, 200],
        'Disp. Qty': [10, 20],
        'O.H Qty': [50, 150],
        'Sold Qty': [30, 70]
    }
    sample_df = pd.DataFrame(sample_data)

    # Converting DataFrame to an Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        sample_df.to_excel(writer, index=False, sheet_name='Sample Data')
    processed_data = output.getvalue()
    return processed_data

def load_data(file):
    return pd.read_excel(file)

def adjust_date(df, threshold_date):
    def adjust_single_date(date):
        threshold_timestamp = pd.Timestamp(threshold_date)
        if date <= threshold_timestamp:
            return threshold_timestamp
        else:
            return date
    df['1st Rcv Date'] = pd.to_datetime(df['1st Rcv Date'])
    df['Adjusted 1st Rcv Date'] = df['1st Rcv Date'].apply(adjust_single_date)
    return df

def aggregate_data(df, threshold_date):
    df = adjust_date(df, threshold_date)
    return df.groupby(['DESIGN', 'STORE_NAME', 'Adjusted 1st Rcv Date']).agg({
        'Shop Rcv Qty': 'sum',
        'Disp. Qty': 'sum',
        'O.H Qty': 'sum',
        'Sold Qty': 'sum'
    }).reset_index()

def calculate_sell_through(desired_df):
    sell_through = (desired_df['Sold Qty'] / (desired_df['Shop Rcv Qty'] - desired_df['Disp. Qty']) * 100)
    sell_through = sell_through.replace([np.inf, -np.inf, np.nan], 0)
    desired_df['shop Sell Through'] = sell_through.astype(int)
    return desired_df

def calculate_days(df):
    current_date = datetime.now()
    df['Days'] = (current_date - df['Adjusted 1st Rcv Date']).dt.days
    return df

def calculate_design_sell_through(df):
    df['Net Receiving'] = df['Shop Rcv Qty'] - df['Disp. Qty']
    design_totals = df.groupby('DESIGN').agg({'Sold Qty': 'sum', 'Net Receiving': 'sum'}).reset_index()
    design_totals['design Sell Through'] = (design_totals['Sold Qty'] / design_totals['Net Receiving'] * 100)
    design_totals['design Sell Through'] = design_totals['design Sell Through'].replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return design_totals

def merge_data(desired_df, design_totals):
    return pd.merge(desired_df, design_totals[['DESIGN', 'design Sell Through']], on='DESIGN', how='left')

def apply_status_condition(desired_df):
    desired_df['Status'] = 'Low'
    desired_df.loc[desired_df['shop Sell Through'] > desired_df['design Sell Through'], 'Status'] = 'High'
    return desired_df

def process_data(desired_df):
    article_days = desired_df.groupby('DESIGN')['Days'].max().reset_index()
    merged_df = pd.merge(desired_df, article_days, on='DESIGN', how='left', suffixes=('', '_max_days'))
    merged_df_grouped = merged_df.groupby('DESIGN').agg({
        'O.H Qty': 'sum',
        'Sold Qty': 'sum',
        'Days': 'max'
    }).reset_index()
    result_df = merged_df_grouped[['DESIGN', 'Days']].rename(columns={'Days': 'Date Difference'})
    return result_df

def process_and_calculate_cover(df, article_days):
    merged_df = pd.merge(df, article_days, on='DESIGN', how='left', suffixes=('', '_max_days'))
    merged_df_grouped = merged_df.groupby('DESIGN').agg({
        'O.H Qty': 'sum',
        'Sold Qty': 'sum',
        'Days': 'max'
    }).reset_index()
    result_df = merged_df_grouped[['DESIGN', 'Days']].rename(columns={'Days': 'Date Difference'})
    merged_df_grouped = pd.merge(merged_df_grouped, result_df, on='DESIGN', how='left')
    merged_df_grouped['desired_cover'] = merged_df_grouped['O.H Qty'] / (merged_df_grouped['Sold Qty'] / merged_df_grouped['Date Difference'])
    return merged_df_grouped

def merge_with_desired_cover(desired_df, merged_df_grouped):
    desired_df = pd.merge(desired_df, merged_df_grouped[['DESIGN', 'desired_cover']], on='DESIGN', how='left')
    desired_df['desired_cover'] = desired_df['desired_cover'].fillna(0).replace([np.inf, -np.inf], 0).astype(int)
    return desired_df

def calculate_article_days(df):
    df['Adjusted 1st Rcv Date'] = pd.to_datetime(df['Adjusted 1st Rcv Date'], errors='coerce')
    df = df.dropna(subset=['Adjusted 1st Rcv Date'])
    today = pd.Timestamp.now().normalize()
    df['Design_Days'] = (today - df['Adjusted 1st Rcv Date']).dt.days
    article_days = df.groupby('DESIGN')['Design_Days'].max().reset_index()
    return article_days

def calculate_required_cover(desired_df):
    desired_df['Transfer in/out'] = desired_df['desired_cover'] * (desired_df['Sold Qty'] / desired_df['Days']) - desired_df['O.H Qty']
    desired_df['Transfer in/out'] = desired_df['Transfer in/out'].replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return desired_df

def merge_desired_with_article_days(desired_df, article_days):
    desired_df = pd.merge(desired_df, article_days, on='DESIGN', how='left')
    return desired_df

def filter_data(desired_df, sell_through_threshold, days_threshold):
    filtered_df = desired_df[(desired_df['design Sell Through'] > sell_through_threshold) & (desired_df['Design_Days'] > days_threshold)]
    return filtered_df

def process_transfer_details(filtered_df):
    sending_stores = filtered_df[filtered_df['Transfer in/out'] < 0]
    receiving_stores = filtered_df[filtered_df['Transfer in/out'] > 0]
    transfer_details = []

    for sending_index, sending_row in sending_stores.iterrows():
        matches = receiving_stores[
            (receiving_stores['DESIGN'] == sending_row['DESIGN']) &
            (receiving_stores['STORE_NAME'] != sending_row['STORE_NAME']) &
            (receiving_stores['Transfer in/out'] > 0)
        ]

        if matches.empty:
            continue

        total_qty_to_transfer = abs(sending_row['Transfer in/out'])

        for receiving_index, receiving_row in matches.iterrows():
            transfer_qty = min(total_qty_to_transfer, receiving_row['Transfer in/out'])
            sending_stores.at[sending_index, 'Transfer in/out'] += transfer_qty
            receiving_stores.at[receiving_index, 'Transfer in/out'] -= transfer_qty
            transfer_details.append({
                'Design': sending_row['DESIGN'],
                'Sending Store': sending_row['STORE_NAME'],
                'Receiving Store': receiving_row['STORE_NAME'],
                'Quantity Transferred': transfer_qty
            })
            total_qty_to_transfer -= transfer_qty
            if total_qty_to_transfer <= 0:
                break

    transfer_df = pd.DataFrame(transfer_details)
    return transfer_df

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    processed_data = output.getvalue()
    return processed_data

def main():
    st.title('Network🌐')
    
    
    sample_file = create_sample_file()
    st.download_button(
        label="Download Sample Excel File",
        data=sample_file,
        file_name='sample_data.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    uploaded_file = st.file_uploader("Upload your Excel file", type=['xlsx'])
    
    if uploaded_file is not None:
        threshold_date = st.date_input("Season Launch Date", min_value=datetime(2020, 1, 1), value=datetime.now())
        sell_through_threshold = st.number_input("Enter Sell-Through Threshold (%)", min_value=0, max_value=100, value=60)
        days_threshold = st.number_input("Enter Minimum Age", min_value=0, max_value=100, value=30)

        if st.button("Process Data"):
            data = load_data(uploaded_file)
            adjusted_data = adjust_date(data, threshold_date)
            aggregated_data = aggregate_data(adjusted_data, threshold_date)
            sell_through_data = calculate_sell_through(aggregated_data)
            days_data = calculate_days(sell_through_data)
            design_sell_through_data = calculate_design_sell_through(days_data)
            merged_data = merge_data(days_data, design_sell_through_data)
            status_data = apply_status_condition(merged_data)
            processed_data = process_data(status_data)
            cover_data = process_and_calculate_cover(status_data, processed_data)
            cover_merged_data = merge_with_desired_cover(status_data, cover_data)
            article_days = calculate_article_days(cover_merged_data)
            required_cover_data = calculate_required_cover(cover_merged_data)
            final_data = merge_desired_with_article_days(required_cover_data, article_days)
            filtered_data = filter_data(final_data, sell_through_threshold, days_threshold)
            transfer_details = process_transfer_details(filtered_data)

            processed_data_excel = to_excel(filtered_data)
            transfer_data_excel = to_excel(transfer_details)

            st.dataframe(filtered_data)

            st.download_button(
                label="Download Processed Data",
                data=processed_data_excel,
                file_name="processed_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="Download Transfer Details",
                data=transfer_data_excel,
                file_name="transfer_details.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
