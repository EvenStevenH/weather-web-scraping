import pandas as pd
import os
import sqlite3
import warnings
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# hide warnings for pandas v2
warnings.simplefilter(action="ignore", category=FutureWarning)

options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
DRIVER = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=options
)
BASE_URL = "https://www.timeanddate.com/weather/usa/new-york/"


# ---------------------------------------------------------------------------- #
def save_files(df, name):
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # save to CSV
    try:
        csv_path = os.path.join(script_dir, "csv", f"{name}.csv")
        df.to_csv(csv_path, index=False)
        print("Data saved to CSV file.")
    except Exception as e:
        print(f"Error saving data to CSV: {e}")

    # save to SQLite database
    try:
        sql_path = os.path.join(script_dir, "db", f"{name}.db")
        conn = sqlite3.connect(sql_path)
        df.to_sql(name="weather_forecast", con=conn, if_exists="replace", index=False)
        conn.close()
        print("Data saved to SQLite database.")
    except sqlite3.Error as e:
        print(f"Error saving data to SQLite database: {e}")


# ---------------------------------------------------------------------------- #
def get_weather_forecast():
    DRIVER.get(BASE_URL + "ext")
    print("\nScraping weather forecast data...")

    # find table with data
    weather_table = WebDriverWait(DRIVER, 10).until(
        EC.presence_of_element_located((By.ID, "wt-ext"))
    )
    if weather_table:
        forecast_data = []
        for row in weather_table.find_elements(By.CSS_SELECTOR, "tbody tr"):
            cells = row.find_elements(By.CSS_SELECTOR, "th, td")

            if len(cells) < 10:
                continue  # skip malformed rows

            day_info = {
                "Day": cells[0].text,
                "Temperature": cells[2].text,
                "Weather": cells[3].text,
                "Feels Like": cells[4].text,
                "Wind": cells[5].text,
                "Humidity": cells[7].text,
                "Chance of Precipitation": cells[8].text,
                "Precipitation Amount": cells[9].text,
            }

            forecast_data.append(day_info)

        # raw data > start cleaning data
        df = pd.DataFrame(forecast_data)
        print("Raw Data:")
        print(df)

        df.dropna(inplace=True)
        df.drop_duplicates(inplace=True)

        # separate temperatures into high/low temp columns
        df["Temperature"] = df["Temperature"].str.rstrip("°F")

        def separate_temperatures(temp_str):
            temp_values = temp_str.split("/")
            return float(temp_values[0].strip()), float(temp_values[1].strip())

        df[["High Temp", "Low Temp"]] = pd.DataFrame(
            df["Temperature"].apply(separate_temperatures).tolist(), index=df.index
        )
        df.drop("Temperature", axis=1, inplace=True)

        # reformat day column
        def reformat_day(day_str):
            month_day = day_str.split("\n")[1].strip()
            current_year = datetime.now().year
            return datetime.strptime(f"{current_year} {month_day}", "%Y %b %d")

        df["Day"] = pd.to_datetime(df["Day"].apply(reformat_day), format="%Y-%m-%d")

        # standardize columns > convert to float
        df["Feels Like"] = df["Feels Like"].str.rstrip("°F")
        df["Wind"] = df["Wind"].str.rstrip("mph")
        df["Humidity"] = df["Humidity"].str.replace("%", "")
        df["Chance of Precipitation"] = df["Chance of Precipitation"].apply(
            lambda value: float(value.strip("%")) / 100.0
        )
        df["Precipitation Amount"] = df["Precipitation Amount"].str.replace('"', "")

        number_columns = [
            "High Temp",
            "Low Temp",
            "Feels Like",
            "Wind",
            "Humidity",
            "Chance of Precipitation",
            "Precipitation Amount",
        ]
        for col in number_columns:
            df[col] = df[col].astype(float)

        # data cleaned > save to CSV and SQLite database
        print("Cleaned Data:")
        print(df)
        save_files(df, "new_york_weather_forecast")


# ---------------------------------------------------------------------------- #
def get_climate_data():
    DRIVER.get(BASE_URL + "climate")
    print("\nScraping climate data...")

    # find table with data
    climate_table = WebDriverWait(DRIVER, 10).until(
        EC.presence_of_element_located((By.ID, "climateTable"))
    )
    if climate_table:
        climate_data = []
        for month in climate_table.find_elements(By.CSS_SELECTOR, ".climate-month"):
            if "allyear" in month.get_attribute("class"):
                continue

            title = (
                month.find_element(By.TAG_NAME, "h3")
                .get_attribute("textContent")
                .strip()
            )
            month_dict = {"Month": title.split(" Climate")[0]}

            for p in month.find_elements(By.TAG_NAME, "p"):
                text = p.get_attribute("textContent").strip()
                key, value = text.split(":", 1)
                month_dict[key.strip()] = value.strip()

            climate_data.append(month_dict)

        # raw data > start cleaning
        df = pd.DataFrame(climate_data)
        print("Raw Data:")
        print(df)

        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)

        # standardize columns > convert to float
        def clean_numeric(column, remove_strings=None):
            cleaned = column.astype(str)
            for item in remove_strings:
                cleaned = cleaned.str.replace(item, "")
            return cleaned.str.strip().astype(float)

        columns = {
            "High Temp": ["°F"],
            "Low Temp": ["°F"],
            "Mean Temp": ["°F"],
            "Dew Point": ["°F"],
            "Wind": ["mph"],
            "Humidity": ["%"],
            "Precipitation": ['"'],
            "Pressure": ['"Hg'],
            "Visibility": ["mi"],
        }
        for column, units in columns.items():
            df[column] = clean_numeric(df[column], units)

        # data cleaned > save to CSV and SQLite database
        print("\nCleaned Data:")
        print(df)
        save_files(df, "new_york_climate")


# ---------------------------------------------------------------------------- #
def main():
    try:
        sleep(2)
        get_weather_forecast()
        sleep(2)
        get_climate_data()

    except Exception as e:
        print(f"Error retrieving web page: {e}.")

    finally:
        DRIVER.quit()


if __name__ == "__main__":
    main()
