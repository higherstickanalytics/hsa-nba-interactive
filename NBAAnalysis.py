import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# File paths
nba_logs_path = 'data/basketball_data/combined_nba_game_logs.csv'
schedule_path = 'data/NBA_Schedule.csv'

# Load data with error checks
if not os.path.exists(nba_logs_path):
    st.error(f"NBA logs file not found at {nba_logs_path}")
    st.stop()

if not os.path.exists(schedule_path):
    st.error(f"Schedule file not found at {schedule_path}")
    st.stop()

nba_logs_df = pd.read_csv(nba_logs_path)
schedule_df = pd.read_csv(schedule_path, parse_dates=['DATE'], dayfirst=False)

# Strip whitespace from columns
nba_logs_df.columns = nba_logs_df.columns.str.strip()

# Rename date column if needed and convert to datetime
if 'GAME_DATE' in nba_logs_df.columns:
    nba_logs_df.rename(columns={'GAME_DATE': 'Date'}, inplace=True)

if 'Date' not in nba_logs_df.columns:
    st.error("No 'Date' or 'GAME_DATE' column found in NBA logs data.")
    st.stop()

nba_logs_df['Date'] = pd.to_datetime(nba_logs_df['Date'], errors='coerce')
nba_logs_df = nba_logs_df.dropna(subset=['Date'])

# Check Player column presence
if 'Player' not in nba_logs_df.columns:
    st.error("No 'Player' column found in NBA logs data.")
    st.stop()

# App title
st.title("NBA Data Viewer with Pie and Time-Series Charts")
st.write("Data from [Basketball Reference](https://www.basketball-reference.com/)")

# Stat mappings (ensure keys match your actual columns)
stat_map = {
    'Points': 'PTS',
    'Assists': 'AST',
    'Rebounds': 'TRB',  # Ensure your CSV has 'TRB' for total rebounds, else 'REB' or 'DREB' + 'OREB'
    'Steals': 'STL',
    'Blocks': 'BLK',
    'Turnovers': 'TOV',
    'Field Goals Made': 'FG',
    'Field Goal Attempts': 'FGA',
    'Three-Pointers Made': '3P',
    'Free Throws Made': 'FT',
    'Personal Fouls': 'PF'
}

# Sidebar: select stat
stat_options = list(stat_map.keys())
selected_stat_display = st.sidebar.selectbox("Select a statistic:", stat_options)
selected_stat = stat_map[selected_stat_display]

# Sidebar: player selection
player_list = nba_logs_df['Player'].dropna().unique().tolist()
selected_player = st.sidebar.selectbox("Select a player:", sorted(player_list))

# Date range selection with valid min/max dates
min_date = nba_logs_df['Date'].min()
max_date = nba_logs_df['Date'].max()

start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

if start_date > end_date:
    st.error("Start Date must be before or equal to End Date.")
    st.stop()

# Filter data by date and player
filtered_df = nba_logs_df[(nba_logs_df['Date'] >= pd.to_datetime(start_date)) & (nba_logs_df['Date'] <= pd.to_datetime(end_date))]
player_df = filtered_df[filtered_df['Player'] == selected_player].copy()

# Convert selected_stat column to numeric, drop NaNs
player_df[selected_stat] = pd.to_numeric(player_df[selected_stat], errors='coerce')
player_df = player_df.dropna(subset=[selected_stat])

# Set threshold slider defaults and limits
max_val = player_df[selected_stat].max() if not player_df.empty else 100.0
default_thresh = player_df[selected_stat].median() if not player_df.empty else 0.0

threshold = st.sidebar.number_input(
    "Set Threshold",
    min_value=0.0,
    max_value=float(max_val) if max_val > 0 else 100.0,
    value=float(default_thresh),
    step=0.5
)

# Pie chart section
st.subheader(f"{selected_stat_display} Distribution for {selected_player}")

stat_counts = player_df[selected_stat].value_counts().sort_index()
if stat_counts.empty:
    st.write("No data available to display pie chart.")
else:
    labels = [f"{int(val)}" if val == int(val) else f"{val:.1f}" for val in stat_counts.index]
    sizes = stat_counts.values

    colors = []
    color_categories = {'green': 0, 'red': 0, 'gray': 0}
    for val, count in zip(stat_counts.index, stat_counts.values):
        if val > threshold:
            colors.append('green')
            color_categories['green'] += count
        elif val < threshold:
            colors.append('red')
            color_categories['red'] += count
        else:
            colors.append('gray')
            color_categories['gray'] += count

    fig1, ax1 = plt.subplots()
    wedges, texts, autotexts = ax1.pie(
        sizes,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
        textprops={'fontsize': 10}
    )
    ax1.axis('equal')
    ax1.set_title(f"{selected_stat_display} Value Distribution")
    st.pyplot(fig1)

    total_entries = sum(color_categories.values())
    st.markdown("**Pie Chart Color Breakdown:**")
    breakdown_df = pd.DataFrame({
        'Color': ['🟩 Green', '🟥 Red', '⬜ Gray'],
        'Category': [
            f"Above {threshold} {selected_stat_display}",
            f"Below {threshold} {selected_stat_display}",
            f"At {threshold} {selected_stat_display}"
        ],
        'Count': [color_categories['green'], color_categories['red'], color_categories['gray']],
        'Percentage': [
            f"{color_categories['green'] / total_entries:.2%}",
            f"{color_categories['red'] / total_entries:.2%}",
            f"{color_categories['gray'] / total_entries:.2%}"
        ]
    })
    st.table(breakdown_df)

# Time-series chart
st.subheader(f"{selected_stat_display} Over Time for {selected_player}")

fig2, ax2 = plt.subplots(figsize=(12, 6))
data = player_df[['Date', selected_stat]].dropna()

if data.empty:
    st.write("No data available in selected date range.")
else:
    bars = ax2.bar(data['Date'], data[selected_stat], color='gray', edgecolor='black')

    count_at_or_above = 0
    for bar, val in zip(bars, data[selected_stat]):
        if val > threshold:
            bar.set_color('green')
            count_at_or_above += 1
        elif val < threshold:
            bar.set_color('red')
        else:
            bar.set_color('gray')
            count_at_or_above += 1

    ax2.axhline(y=threshold, color='blue', linestyle='--', linewidth=2, label=f'Threshold: {threshold}')
    ax2.set_xlabel("Date")
    ax2.set_ylabel(selected_stat_display)
    ax2.set_title(f"{selected_stat_display} Over Time")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig2.autofmt_xdate()
    ax2.legend()
    st.pyplot(fig2)

    total_games = len(data)
    st.write(f"Games at or above threshold: {count_at_or_above}/{total_games} ({count_at_or_above / total_games:.2%})")
