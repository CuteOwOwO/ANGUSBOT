import discord
from discord.ext import commands
import requests
import json
import os # 導入 os 模組

# 從 .env 檔案載入環境變數
# 注意：在 Cog 中，通常 main.py 會統一載入 dotenv
# 但為了這個單獨的 Cog 也能獨立測試，可以重複載入一次，或者假設 main.py 已經處理。
# 如果 main.py 已經有 load_dotenv()，這裡可以移除。
# from dotenv import load_dotenv
# load_dotenv() 

# 從環境變數中讀取氣象局 API Key
CWA_API_KEY = os.getenv('CWA_API_KEY')

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 檢查 API Key 是否存在
        if not CWA_API_KEY:
            print("警告: 未找到 CWA_API_KEY 環境變數。天氣查詢功能將無法使用。")
            # 可以在這裡設置一個標誌，防止嘗試呼叫 API
            self.api_available = False
        else:
            self.api_available = True
            self.base_url = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?'
            self.headers = {
                'accept': 'application/json'
            }
            # 你可以定義一個測站字典，方便用戶查詢不同地區
            self.stations = {
                '信義': 'C0AC70',
                #'大安': 'C0AC80', # 假設大安區測站ID，請替換為實際值
                #'士林': 'C0AD10', # 假設士林區測站ID，請替換為實際值
                # 添加更多你感興趣的測站
            }
            self.TRIGGER_KEYWORDS = ["出門", "天氣", "氣溫"]
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        user_id = message.author.id
        cleaned_content = message.clean_content.strip()
        
        if self.bot.user in message.mentions and any(keyword in cleaned_content for keyword in self.TRIGGER_KEYWORDS):
            if not self.api_available:
                await message.channel.send("抱歉，天氣查詢功能目前不可用。請稍後再試。")
                return
        try:
            # 使用 base_url 和 params 字典發送 GET 請求
            response = requests.get(self.base_url, params=self.params, headers=self.headers)
            response.raise_for_status()  # 檢查請求是否成功 (HTTP 狀態碼 200)

            data = response.json() # 將回應內容解析為 JSON
            print(json.dumps(data, indent=4, ensure_ascii=False)) # 美化輸出並處理中文

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            
        if data.get('success') == 'true':
            stations = data.get('records', {}).get('Station', [])
            
            if not stations:
                print("在 JSON 資料中找不到任何測站資訊。")
                return

            for station in stations: # 遍歷所有測站，雖然您的範例只有一個
                station_name = station.get('StationName') 
                station_id = station.get('StationId') 
                obs_time = station.get('ObsTime', {}).get('DateTime') 

                print(f"--- 測站名稱：{station_name} (ID: {station_id}) ---")
                print(f"觀測時間：{obs_time}")

                geo_info = station.get('GeoInfo', {})
                county_name = geo_info.get('CountyName')
                town_name = geo_info.get('TownName')
                station_altitude = geo_info.get('StationAltitude')

                print(f"地理位置：{county_name}{town_name}")
                print(f"測站海拔：{station_altitude} 公尺")

                coordinates = geo_info.get('Coordinates', [])
                for coord in coordinates:
                    coord_name = coord.get('CoordinateName')
                    latitude = coord.get('StationLatitude')
                    longitude = coord.get('StationLongitude')
                    print(f"  {coord_name} 座標：緯度 {latitude}, 經度 {longitude}")

                weather_element = station.get('WeatherElement', {})

                # 提取各項天氣要素
                weather = weather_element.get('Weather')
                precipitation = weather_element.get('Now', {}).get('Precipitation')
                wind_direction = weather_element.get('WindDirection')
                wind_speed = weather_element.get('WindSpeed')
                air_temperature = weather_element.get('AirTemperature')
                relative_humidity = weather_element.get('RelativeHumidity')
                air_pressure = weather_element.get('AirPressure')
                uv_index = weather_element.get('UVIndex')

                print(f"\n天氣狀況：{weather}")
                print(f"目前降雨量：{precipitation} mm")
                print(f"風向：{wind_direction}°")
                print(f"風速：{wind_speed} m/s")
                print(f"氣溫：{air_temperature}°C")
                print(f"相對濕度：{relative_humidity}%")
                print(f"氣壓：{air_pressure} hPa")
                print(f"紫外線指數：{uv_index}")

                # 提取陣風資訊
                gust_info = weather_element.get('GustInfo', {})
                peak_gust_speed = gust_info.get('PeakGustSpeed')
                gust_wind_direction = gust_info.get('Occurred_at', {}).get('WindDirection')
                gust_datetime = gust_info.get('Occurred_at', {}).get('DateTime')
                if peak_gust_speed and peak_gust_speed != "-99": # 檢查是否有有效數據
                    print(f"最大陣風：{peak_gust_speed} m/s (方向: {gust_wind_direction}°, 時間: {gust_datetime})")
                else:
                    print("最大陣風資訊：無有效數據或未記錄")

                # 提取每日極值 (最高溫和最低溫)
                daily_extreme = weather_element.get('DailyExtreme', {})

                daily_high_info = daily_extreme.get('DailyHigh', {}).get('TemperatureInfo', {})
                daily_high_temperature = daily_high_info.get('AirTemperature')
                daily_high_time = daily_high_info.get('Occurred_at', {}).get('DateTime')
                print(f"每日最高氣溫：{daily_high_temperature}°C (發生時間: {daily_high_time})")

                daily_low_info = daily_extreme.get('DailyLow', {}).get('TemperatureInfo', {})
                daily_low_temperature = daily_low_info.get('AirTemperature')
                daily_low_time = daily_low_info.get('Occurred_at', {}).get('DateTime')
                print(f"每日最低氣溫：{daily_low_temperature}°C (發生時間: {daily_low_time})")

                print("-" * 30) # 分隔不同測站的資訊
        else:
            print(f"API 請求未成功：{data.get('success')}") 
            
           
       

        

# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(Weather(bot))