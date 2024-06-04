import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from io import BytesIO

def create_sample_file():
    # Creating a sample DataFrame with the required headers
    sample_data = {
        'Zone': ['Zone1', 'Zone2'],
        'STORE_NAME': ['Store1', 'Store2'],
        '1st Rcv Date': [datetime(2023, 1, 1), datetime(2023, 1, 2)],
        'DESIGN': ['Design1', 'Design2'],
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
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip()  # Strip any leading/trailing whitespace from column names
    return df

def adjust_date(df, threshold_date):
    threshold_timestamp = pd.Timestamp(threshold_date)
    df['1st Rcv Date'] = pd.to_datetime(df['1st Rcv Date'], errors='coerce')
    df = df.dropna(subset=['1st Rcv Date'])  # Remove rows where date conversion failed
    df['Adjusted 1st Rcv Date'] = np.where(df['1st Rcv Date'] <= threshold_timestamp, threshold_timestamp, df['1st Rcv Date'])
    return df

def aggregate_data(df):
    df['Adjusted 1st Rcv Date'] = pd.to_datetime(df['Adjusted 1st Rcv Date'], errors='coerce')
    df = df.dropna(subset=['Adjusted 1st Rcv Date'])  # Remove rows where date conversion failed
    return df.groupby(['Zone', 'STORE_NAME', 'Adjusted 1st Rcv Date', 'DESIGN']).agg({
        'Shop Rcv Qty': 'sum',
        'Disp. Qty': 'sum',
        'O.H Qty': 'sum',
        'Sold Qty': 'sum'
    }).reset_index()

def calculate_sell_through(desired_df):
    desired_df['shop design Sell Through'] = (desired_df['Sold Qty'] / (desired_df['Shop Rcv Qty'] - desired_df['Disp. Qty']) * 100).replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return desired_df

def calculate_days(df):
    current_date = datetime.now()
    df['Days'] = (current_date - df['Adjusted 1st Rcv Date']).dt.days
    return df

def calculate_zone_design_sell_through(df):
    df['Net Receiving'] = df['Shop Rcv Qty'] - df['Disp. Qty']
    zone_design_totals = df.groupby(['Zone', 'DESIGN']).agg({'Sold Qty': 'sum', 'Net Receiving': 'sum'}).reset_index()
    zone_design_totals['zone design Sell Through'] = (zone_design_totals['Sold Qty'] / zone_design_totals['Net Receiving'] * 100).replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return zone_design_totals

def merge_data(desired_df, zone_design_totals):
    return pd.merge(desired_df, zone_design_totals[['Zone', 'DESIGN', 'zone design Sell Through']], on=['Zone', 'DESIGN'], how='left')

def apply_status_condition(desired_df):
    desired_df['Status'] = np.where(desired_df['shop design Sell Through'] > desired_df['zone design Sell Through'], 'High', 'Low')
    return desired_df

def process_data(desired_df):
    article_days = desired_df.groupby('Zone')['Days'].max().reset_index()
    merged_df = pd.merge(desired_df, article_days, on='Zone', how='left', suffixes=('', '_max_days'))
    merged_df_grouped = merged_df.groupby('Zone').agg({
        'O.H Qty': 'sum',
        'Sold Qty': 'sum',
        'Days': 'max'
    }).reset_index()
    result_df = merged_df_grouped[['Zone', 'Days']].rename(columns={'Days': 'Date Difference'})
    return result_df

def process_and_calculate_cover(df, article_days):
    merged_df = pd.merge(df, article_days, on='Zone', how='left', suffixes=('', '_max_days'))
    merged_df_grouped = merged_df.groupby('Zone').agg({
        'O.H Qty': 'sum',
        'Sold Qty': 'sum',
        'Days': 'max'
    }).reset_index()
    result_df = merged_df_grouped[['Zone', 'Days']].rename(columns={'Days': 'Date Difference'})
    merged_df_grouped = pd.merge(merged_df_grouped, result_df, on='Zone', how='left')
    merged_df_grouped['desired_cover'] = (merged_df_grouped['O.H Qty'] / (merged_df_grouped['Sold Qty'] / merged_df_grouped['Date Difference'])).replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return merged_df_grouped

def merge_with_desired_cover(desired_df, merged_df_grouped):
    desired_df = pd.merge(desired_df, merged_df_grouped[['Zone', 'desired_cover']], on='Zone', how='left')
    desired_df['desired_cover'] = desired_df['desired_cover'].fillna(0).astype(int)
    return desired_df

def calculate_article_days(df):
    df['Adjusted 1st Rcv Date'] = pd.to_datetime(df['Adjusted 1st Rcv Date'], errors='coerce')
    df = df.dropna(subset=['Adjusted 1st Rcv Date'])
    today = pd.Timestamp.now().normalize()
    df['Zone_Days'] = (today - df['Adjusted 1st Rcv Date']).dt.days
    article_days = df.groupby('Zone')['Zone_Days'].max().reset_index()
    return article_days

def calculate_required_cover(desired_df):
    desired_df['Transfer in/out'] = (desired_df['desired_cover'] * (desired_df['Sold Qty'] / desired_df['Days']) - desired_df['O.H Qty']).replace([np.inf, -np.inf, np.nan], 0).astype(int)
    return desired_df

def merge_desired_with_article_days(desired_df, article_days):
    desired_df = pd.merge(desired_df, article_days, on='Zone', how='left')
    return desired_df

def filter_data(desired_df, sell_through_threshold, days_threshold):
    return desired_df[(desired_df['zone design Sell Through'] > sell_through_threshold) & (desired_df['Zone_Days'] > days_threshold)]

def process_transfer_details(filtered_df):
    sending_stores = filtered_df[filtered_df['Transfer in/out'] > 0]
    receiving_stores = filtered_df[filtered_df['Transfer in/out'] < 0]
    transfer_details = []

    for receiving_index, receiving_row in receiving_stores.iterrows():
        # Ensure that the receiving store does not appear in sending stores with the same DESIGN
        matches = sending_stores[
            (sending_stores['Zone'] == receiving_row['Zone']) &
            (sending_stores['STORE_NAME'] != receiving_row['STORE_NAME']) &  # Ensure the store names are not the same
            (sending_stores['DESIGN'] == receiving_row['DESIGN']) &  # Match on the same DESIGN
            (sending_stores['Transfer in/out'] > 0)
        ]

        if matches.empty:
            continue

        total_qty_needed = abs(receiving_row['Transfer in/out'])

        for sending_index, sending_row in matches.iterrows():
            transfer_qty = min(total_qty_needed, sending_row['Transfer in/out'])
            receiving_stores.at[receiving_index, 'Transfer in/out'] += transfer_qty
            sending_stores.at[sending_index, 'Transfer in/out'] -= transfer_qty
            transfer_details.append({
                'Zone': receiving_row['Zone'],
                'Sending Store': sending_row['STORE_NAME'],
                'Receiving Store': receiving_row['STORE_NAME'],
                'Quantity Transferred': transfer_qty,
                'DESIGN': sending_row['DESIGN']
            })
            total_qty_needed -= transfer_qty
            if total_qty_needed <= 0:
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
    st.title('Regional🌏')

    # Provide the sample file for download
    
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

        if st.button("Process Data") or 'filtered_data' not in st.session_state:
            data = load_data(uploaded_file)
            adjusted_data = adjust_date(data, threshold_date)
            aggregated_data = aggregate_data(adjusted_data)
            sell_through_data = calculate_sell_through(aggregated_data)
            days_data = calculate_days(sell_through_data)
            zone_design_sell_through_data = calculate_zone_design_sell_through(days_data)
            merged_data = merge_data(days_data, zone_design_sell_through_data)
            status_data = apply_status_condition(merged_data)
            processed_data = process_data(status_data)
            cover_data = process_and_calculate_cover(status_data, processed_data)
            cover_merged_data = merge_with_desired_cover(status_data, cover_data)
            article_days = calculate_article_days(cover_merged_data)
            required_cover_data = calculate_required_cover(cover_merged_data)
            final_data = merge_desired_with_article_days(required_cover_data, article_days)
            filtered_data = filter_data(final_data, sell_through_threshold, days_threshold)
            transfer_details = process_transfer_details(filtered_data)

            # Store the processed data and transfer details in session state
            st.session_state.filtered_data = filtered_data
            st.session_state.transfer_details = transfer_details

        # Load from session state
        filtered_data = st.session_state.filtered_data
        transfer_details = st.session_state.transfer_details

        processed_data_bytes = to_excel(filtered_data)
        transfer_data_bytes = to_excel(transfer_details)

        st.dataframe(filtered_data)

        st.download_button(
            label="Download Processed Data",
            data=processed_data_bytes,
            file_name="processed_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.download_button(
            label="Download Transfer Details",
            data=transfer_data_bytes,
            file_name="transfer_details.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
