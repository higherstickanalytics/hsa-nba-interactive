import streamlit as st
import pandas as pd

# Paths to the files
nba_logs_path = 'data/basketball_data/combined_nba_game_logs.csv'
schedule_path = 'data/NBA_Schedule.csv'

# Load the data
nba_logs_df = pd.read_csv(nba_logs_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['DATE'], dayfirst=False)

# Title of the app
st.title("NBA Data Viewer")

# Display the first 5 rows of each dataset
st.subheader("First 5 Rows of NBA Game Logs")
st.dataframe(nba_logs_df.head())

st.subheader("First 5 Rows of NBA Schedule Data")
st.dataframe(schedule_df.head())
