import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col

# **🔥 Initialize Spark Session**
spark = SparkSession.builder.appName("ClimateAnalysis").getOrCreate()

# **📂 Load Dataset**
data_path = "GlobalWeatherRepository.csv"

try:
    df = pd.read_csv(data_path)
    spark_df = spark.read.csv(data_path, header=True, inferSchema=True)
except FileNotFoundError:
    st.error(f"❌ File not found: {data_path}")
    st.stop()

# **📌 Page Configurations**
st.set_page_config(
    page_title="Climate Analysis Dashboard",
    page_icon="🌍",
    layout="wide"
)

# **🎨 Custom CSS for Styling**
st.markdown("""
    <style>
        .title { text-align: center; font-size: 36px; font-weight: bold; color: #2E8B57; }
        .subtitle { text-align: center; font-size: 22px; color: #555; }
        .sidebar { background-color: #f7f7f7; padding: 20px; }
    </style>
""", unsafe_allow_html=True)

# **🌍 Main Title**
st.markdown("<h1 class='title'>🌍 Climate Analysis Dashboard</h1>", unsafe_allow_html=True)

# **🌎 Sidebar: Country Selection**
st.sidebar.header("🌎 Filter Data")

if "country" not in df.columns:
    st.error("❌ The dataset is missing the 'country' column!")
    st.stop()

country_list = ["Select a country"] + list(df["country"].unique())
selected_country = st.sidebar.selectbox("🌍 Select a Country", country_list)

# **Show Data Only When Country is Selected**
if selected_country == "Select a country":
    st.sidebar.info("📌 Please select a country from the dropdown to begin.")

    # **Display an Image**
    st.image("https://kraaijenbrink.github.io/earthengine-workshop/figures/banner_4.jpg", use_container_width=True)
    st.markdown("<h3 class='subtitle'>🌱 Welcome to the Climate Dashboard!</h3>", unsafe_allow_html=True)
    st.markdown("""
        This dashboard provides **interactive climate analysis** based on real-time weather data.  
        - 📊 **Temperature Trends**  
        - 💧 **Humidity & Precipitation**  
        - 💨 **Wind Speed & Air Quality**  
        - 🌞 **UV Index & Extreme Weather**  
        
        **Select a country from the sidebar** to begin exploring data.
    """)
    st.stop()  # Stops execution until a country is selected

# **📊 Filter Data for Selected Country**
filtered_df = df[df["country"] == selected_country]

# **📋 Dataset Overview**
st.subheader(f"📄 Dataset Overview - {selected_country}")
st.dataframe(filtered_df.describe())

# **🌡️ Temperature & Humidity Trends**
st.subheader("🌡️ Temperature & Humidity Trends")
fig, ax1 = plt.subplots(figsize=(12, 5))

ax1.plot(filtered_df["temperature_celsius"], label="Temperature (°C)", color="green")
ax2 = ax1.twinx()
ax2.plot(filtered_df["humidity"], label="Humidity (%)", color="blue")

ax1.set_xlabel("Time")
ax1.set_ylabel("Temperature (°C)", color="green")
ax2.set_ylabel("Humidity (%)", color="blue")

ax1.legend(loc="upper left")
ax2.legend(loc="upper right")
st.pyplot(fig)

# **🌬️ Air Quality Index**
st.subheader("🌬️ Air Quality Index")
air_quality_cols = ["air_quality_PM2.5", "air_quality_PM10", "air_quality_Ozone", "air_quality_Nitrogen_dioxide"]
valid_cols = [col for col in air_quality_cols if col in filtered_df.columns]

if valid_cols:
    st.bar_chart(filtered_df[valid_cols])
else:
    st.warning("⚠️ Air quality data not available.")

# **💨 Wind Speed Distribution**
st.subheader("💨 Wind Speed Distribution")
if "wind_kph" in filtered_df.columns:
    fig, ax = plt.subplots()
    ax.hist(filtered_df["wind_kph"], bins=20, color="skyblue", edgecolor="black")
    ax.set_title("Wind Speed Distribution")
    ax.set_xlabel("Wind Speed (km/h)")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)
else:
    st.warning("⚠️ Wind speed data not available.")

# **📊 Correlation Heatmap (Enhanced)**

st.subheader("📉 Correlation Heatmap")

# Select only numeric columns
numeric_df = filtered_df.select_dtypes(include=[np.number])

if not numeric_df.empty:
    # Drop columns with low variance to reduce clutter
    numeric_df = numeric_df.loc[:, numeric_df.std() > 0.1]

    # Compute correlation matrix
    corr_matrix = numeric_df.corr()

    # Mask the upper triangle to remove redundant information
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

    # Create the heatmap
    fig, ax = plt.subplots(figsize=(12, 8))  # Increase figure size
    sns.heatmap(
        corr_matrix, 
        mask=mask,  # Hide upper triangle
        annot=True, 
        fmt=".2f",  # Round values for better readability
        cmap="coolwarm", 
        vmin=-1, vmax=1, 
        linewidths=0.5, 
        square=True,
        cbar_kws={"shrink": 0.8}  # Shrink color bar
    )

    st.pyplot(fig)
else:
    st.warning("⚠️ No numeric data available for correlation analysis.")

# **🌧️ Precipitation Analysis**
if "precip_mm" in filtered_df.columns:
    st.subheader("🌧️ Precipitation Analysis")
    st.line_chart(filtered_df["precip_mm"])
else:
    st.warning("⚠️ Precipitation data missing.")

# **☀️ UV Index Analysis**
if "uv_index" in filtered_df.columns:
    st.subheader("☀️ UV Index Distribution")
    fig, ax = plt.subplots()
    ax.hist(filtered_df["uv_index"], bins=10, color="gold", edgecolor="black")
    ax.set_title("UV Index Distribution")
    ax.set_xlabel("UV Index")
    ax.set_ylabel("Frequency")
    st.pyplot(fig)
else:
    st.warning("⚠️ UV Index data not available.")

# **⚡ Spark Data Processing Example**
st.subheader("⚡ Spark Data Processing Example")
if "temperature_celsius" in spark_df.columns and "country" in spark_df.columns:
    country_avg_temp = (
        spark_df.groupBy("country")
        .agg(avg("temperature_celsius").alias("avg_temp"))
        .orderBy(col("avg_temp").desc())
    )

    st.dataframe(country_avg_temp.toPandas())  # Convert Spark DF to Pandas for better display
else:
    st.warning("⚠️ Spark data is missing required columns.")

# **🌪️ Extreme Weather Conditions**
st.subheader("🌪️ Extreme Weather Conditions")
if "temperature_celsius" in filtered_df.columns:
    st.write(filtered_df[filtered_df["temperature_celsius"] > 40])
if "wind_kph" in filtered_df.columns:
    st.write(filtered_df[filtered_df["wind_kph"] > 80])

# **🌅 Sunrise & Sunset Visualization**
if "sunrise" in filtered_df.columns and "sunset" in filtered_df.columns:
    st.subheader("🌅 Sunrise & Sunset Times")
    st.line_chart(filtered_df[["sunrise", "sunset"]])
else:
    st.warning("⚠️ Sunrise and sunset data not available.")

# Footer
st.markdown("---")
st.markdown("**📌 Developed by MAYANK YADAV** | Data powered by **GlobalWeatherData** 🌍")
