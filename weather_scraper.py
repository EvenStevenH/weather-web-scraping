import pandas as pd
import os
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

# driver settings
options = webdriver.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
driver = webdriver.Chrome(
    service=ChromeService(ChromeDriverManager().install()), options=options
)

BASE_URL = "https://www.timeanddate.com/weather/usa/new-york/"


# ---------------------------------------------------------------------------- #
def get_weather_forecast():
    driver.get(BASE_URL + "ext")

    # find table with data > wait as long as needed
    weather_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "wt-ext"))
    )
    if weather_table:
        rows = weather_table.find_elements(By.CSS_SELECTOR, "tbody tr")
        forecast_data = []
        for row in rows:
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

        # raw data
        df = pd.DataFrame(forecast_data)
        print("Raw data:")
        print(df)

        # start cleaning data
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

        # data cleaning done
        print("Cleaned data:")
        print(df)

        # save to CSV
        script_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(script_dir, "csv", "new_york_weather_forecast.csv")
        df.to_csv(csv_path, index=False)
        print("Weather forecast data saved to CSV file.")


# ---------------------------------------------------------------------------- #
def main():
    try:
        get_weather_forecast()
        # sleep(4)

    except Exception as e:
        print("Error when retrieving web page.")
        print(f"Exception: {type(e).__name__} {e}.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
