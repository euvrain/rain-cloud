
import pandas as pd
import requests_cache
from retry_requests import retry

lcd_df = pd.read_csv("data/lcd_d.csv", low_memory=False)
storm_df_2018 = pd.read_csv("data/StormEvents_fatalities-ftp_v1.0_d2018_c20260224.csv", low_memory=False)
storm_df_2019 = pd.read_csv("data/StormEvents_fatalities-ftp_v1.0_d2019_c20260116.csv", low_memory=False)

print("=== LCD ===")
print(lcd_df.columns.tolist())
print(lcd_df.head(2))
print(lcd_df.dtypes[['DATE', 'HourlyWindSpeed', 'HourlyStationPressure']].to_string())

print("\n=== STORM EVENTS ===")
print(storm_df.columns.tolist())
print(storm_df.head(2))
print(storm_df.dtypes[['BEGIN_DATE_TIME', 'STATE', 'EVENT_TYPE']].to_string())

#Open - Meteo API for live weather forecasts
import openmeteo_requests
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 40.07,
	"longitude": 74.72,
	"hourly": ["precipitation_probability", "cape"],
	"current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "wind_gusts_10m", "precipitation", "surface_pressure"],
	"timezone": "America/New_York",
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation: {response.Elevation()} m asl")
print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

# Process current data. The order of variables needs to be the same as requested.
current = response.Current()
current_temperature_2m = current.Variables(0).Value()
current_relative_humidity_2m = current.Variables(1).Value()
current_wind_speed_10m = current.Variables(2).Value()
current_wind_gusts_10m = current.Variables(3).Value()
current_precipitation = current.Variables(4).Value()
current_surface_pressure = current.Variables(5).Value()

current_temperature_2m_f = current_temperature_2m * 9/5 + 32
print(f"\nCurrent time: {current.Time()}")
print(f"Current temperature_2m (F): {current_temperature_2m_f:.1f}°F")
print(f"Current relative_humidity_2m: {current_relative_humidity_2m}")
print(f"Current wind_speed_10m: {current_wind_speed_10m}")
print(f"Current wind_gusts_10m: {current_wind_gusts_10m}")
print(f"Current precipitation: {current_precipitation}")
print(f"Current surface_pressure: {current_surface_pressure}")

# Process hourly data. The order of variables needs to be the same as requested.
hourly = response.Hourly()
hourly_precipitation_probability = hourly.Variables(0).ValuesAsNumpy()
hourly_cape = hourly.Variables(1).ValuesAsNumpy()

hourly_data = {"date": pd.date_range(
	start = pd.to_datetime(hourly.Time() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	end =  pd.to_datetime(hourly.TimeEnd() + response.UtcOffsetSeconds(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = hourly.Interval()),
	inclusive = "left"
)}

hourly_data["precipitation_probability"] = hourly_precipitation_probability
hourly_data["cape"] = hourly_cape

hourly_dataframe = pd.DataFrame(data = hourly_data)
print("\nHourly data\n", hourly_dataframe)

#feature engineering
wind_gust_ratio = current_wind_gusts_10m / current_wind_speed_10m if current_wind_speed_10m != 0 else 0