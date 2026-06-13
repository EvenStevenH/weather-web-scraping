import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# page config > load datasets
st.set_page_config(
    page_title="New York Weather Dashboard", page_icon="🌤️", layout="wide"
)
forecast_df = pd.read_csv("./csv/new_york_weather_forecast.csv")
climate_df = pd.read_csv("./csv/new_york_climate.csv")

# ---------------------------------------------------------------------------- #
# sidebar
st.sidebar.title("Controls")
app_mode = st.sidebar.radio(
    "Select View", ["Overview", "Weather Forecast", "Climate Trends"]
)
st.sidebar.markdown("---")


# ---------------------------------------------------------------------------- #
if app_mode == "Overview":
    st.title("New York Weather Insights")
    st.markdown("""
        Welcome! This dashboard visualizes weather patterns for **New York**. Use the sidebar to navigate between a **short-term forecast** and **long-term climate trends**.
        """)

    col1, col2, col3 = st.columns(3)

    if forecast_df is not None:
        with col1:
            st.metric("Forecast Days", len(forecast_df))
        with col2:
            avg_temp = forecast_df["High Temp"].mean()
            st.metric("Avg Forecast High", f"{avg_temp:.1f}°F")
        with col3:
            max_precip = forecast_df["Precipitation Amount"].max()
            st.metric("Max Precipitation Recorded", f'{max_precip:.2f}"')

    if climate_df is not None:
        st.markdown("### Climate Summary")
        st.dataframe(climate_df, width="stretch")

    else:
        st.error("Data files not found. Please run scraper.py first!")

# ---------------------------------------------------------------------------- #
elif app_mode == "Weather Forecast":
    st.title("15-Day Weather Forecast")

    if forecast_df is None:
        st.error("Forecast data missing.")
    else:
        st.sidebar.subheader("Filters")  # filter > temperature range
        min_high_temp = float(forecast_df["High Temp"].min())
        max_high_temp = float(forecast_df["High Temp"].max())
        min_low_temp = float(forecast_df["Low Temp"].min())
        max_low_temp = float(forecast_df["Low Temp"].max())
        high_temp_range = st.sidebar.slider(
            "High Temperature Range (°F)",
            min_high_temp,
            max_high_temp,
            (min_high_temp, max_high_temp),
        )
        low_temp_range = st.sidebar.slider(
            "Low Temperature Range (°F)",
            min_low_temp,
            max_low_temp,
            (min_low_temp, max_low_temp),
        )
        filtered_df = forecast_df[
            (forecast_df["High Temp"] >= high_temp_range[0])
            & (forecast_df["High Temp"] <= high_temp_range[1])
            & (forecast_df["Low Temp"] >= low_temp_range[0])
            & (forecast_df["Low Temp"] <= low_temp_range[1])
        ]

        if filtered_df.empty:
            st.warning("No data matches the selected temperature range.")
        else:
            fig_temp = px.line(  # temperature trend line
                filtered_df,
                x="Day",
                y=["High Temp", "Low Temp"],
                title="Temperature Fluctuations (High vs Low)",
                labels={"value": "Temperature (°F)", "variable": "Type"},
                markers=True,
            )
            st.plotly_chart(fig_temp, width="stretch")

            col_left, col_right = st.columns(2)
            with col_left:  # precipitation bar chart
                fig_precip = px.bar(
                    filtered_df,
                    x="Day",
                    y="Precipitation Amount",
                    title="Precipitation Amount (inches)",
                    color="Precipitation Amount",
                    color_continuous_scale="Greens",
                )
                st.plotly_chart(fig_precip, width="stretch")
            with col_right:  # humidity vs wind speed scatter
                fig_scatter = px.scatter(
                    filtered_df,
                    x="Humidity",
                    y="Wind",
                    size="Precipitation Amount",
                    color="Weather",
                    title="Humidity vs Wind Speed",
                    hover_name="Day",
                )
                st.plotly_chart(fig_scatter, width="stretch")
                st.info("Size = Precipitation")

            with st.expander("View Raw Forecast Data"):  # raw data
                st.write(filtered_df)

# ---------------------------------------------------------------------------- #
elif app_mode == "Climate Trends":
    st.title("Climate Trends")

    if climate_df is None:
        st.error("Climate data missing.")
    else:
        st.sidebar.subheader("Filters")  # filter by month
        months = st.sidebar.multiselect(
            "Select Months to Compare",
            options=climate_df["Month"].unique(),
            default=climate_df["Month"].unique(),
        )
        filtered_climate = climate_df[climate_df["Month"].isin(months)]

        if filtered_climate.empty:
            st.warning("Please select at least one month.")
        else:
            fig_climate_temp = go.Figure()  # monthly temperature comparison
            fig_climate_temp.add_trace(
                go.Scatter(
                    x=filtered_climate["Month"],
                    y=filtered_climate["High Temp"],
                    mode="lines+markers",
                    name="High Temp",
                    line=dict(color="red"),
                )
            )
            fig_climate_temp.add_trace(
                go.Scatter(
                    x=filtered_climate["Month"],
                    y=filtered_climate["Low Temp"],
                    mode="lines+markers",
                    name="Low Temp",
                    line=dict(color="orange"),
                )
            )
            fig_climate_temp.update_layout(
                title="Monthly Temperature",
                xaxis_title="Month",
                yaxis_title="°F",
            )
            st.plotly_chart(fig_climate_temp, width="stretch")

            col_a, col_b = st.columns(2)
            with col_a:  # precipitation by month
                fig_precip_climate = px.bar(
                    filtered_climate,
                    x="Month",
                    y="Precipitation",
                    title="Monthly Average Precipitation (inches)",
                    color="Precipitation",
                    color_continuous_scale="Greens",
                )
                st.plotly_chart(fig_precip_climate, width="stretch")
            with col_b:  # humidity vs dew point
                fig_dew = px.scatter(
                    filtered_climate,
                    x="Humidity",
                    y="Dew Point",
                    size="Wind",
                    text="Month",
                    title="Humidity vs Dew Point, by Month",
                )
                st.plotly_chart(fig_dew, width="stretch")
                st.info("Size = Wind Speed")

            with st.expander("View Raw Climate Data"):  # raw data
                st.write(filtered_climate)
