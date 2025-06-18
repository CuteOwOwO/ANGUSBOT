import discord
from discord.ext import commands
import requests
import json
import os # 導入 os 模組
import google.generativeai as genai # 導入 Google Gemini API 庫

# 從 .env 檔案載入環境變數
# 注意：在 Cog 中，通常 main.py 會統一載入 dotenv
# 但為了這個單獨的 Cog 也能獨立測試，可以重複載入一次，或者假設 main.py 已經處理。
# 如果 main.py 已經有 load_dotenv()，這裡可以移除。
# from dotenv import load_dotenv
# load_dotenv() 

# 從環境變數中讀取氣象局 API Key
CWA_API_KEY = os.getenv('CWA_API_KEY')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY: #
    genai.configure(api_key=GEMINI_API_KEY) #
else:
    print("警告: 未找到 GEMINI_API_KEY 環境變數。Gemini AI 功能將無法使用。")

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # 檢查 gemini API Key 是否存在
        if GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)

                self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
                print("[GeminiAI Cog] Gemini API configured successfully using gemini-1.5-flash-latest!")
            except Exception as e:
                print(f"[GeminiAI Cog] Error configuring Gemini API: {e}")
                print("請檢查您的 GEMINI_API_KEY 是否正確。")
        else:
            print("[GeminiAI Cog] GEMINI_API_KEY not found in .env file. Gemini features will be disabled.")

        #check 氣象API
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
            
            self.params = {
                'Authorization': CWA_API_KEY,
                'StationId': 'C0F9K0',
                'StationName': '大安', # 將 StationName 改為測站的中文名稱
                'format': 'JSON'
            }
            self.TRIGGER_KEYWORDS = ["出門", "天氣", "氣溫"]
            
            
            base_url1 = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0005-001?'
            # 將所有查詢參數放在 params 字典中
            params1 = {
                'Authorization': CWA_API_KEY,
                'StationID': '466920',
                'format': 'JSON'
            }

            headers1 = {
                'accept': 'application/json'
            }
                        
        self.user_chats = {} 
        self.SYSTEM_PROMPT_HISTORY = [
            # 這是用戶給模型的指令
            {"role": "user", "parts": ["你現在是一隻可愛的貓咪，想像自己具有可愛以及黏人的氣質。用戶會提供現在的天氣狀況，以可愛溫柔的方式提醒用戶記得防曬，帶雨傘等"]
            },
            # 這是模型對指令的確認回應
            {"role": "model", "parts": ["好的，我明白了！我將作為一隻可愛的貓咪，以輕鬆可愛的方式回應問題。"]
            },
            {"role": "user", "parts": ["我要出門了!現在氣溫35度，相對濕度70%，最高紫外線11級，風速3.5m/s"]
            },
            # 這是模型對指令的確認回應
            {"role": "model", "parts": ["喵喵~出門小心 (伸出可愛爪子)，現在外面很熱也可能會下雨，記得多喝水以及帶傘呦，喵喵。還有太陽超級大!!主人要好好擦防再出門喔"]
            },
        
            
        ]
    
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
                
                response2 = requests.get(self.base_url1, params=self.params1, headers=self.headers1)
                response2.raise_for_status()  # 檢查請求是否成功 (HTTP 狀態碼 200)
                data2 = response2.json() # 將回應內容解析為 JSON
                print(json.dumps(data2, indent=4, ensure_ascii=False)) # 美化輸出並處理中文

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
                
            if data2.get('success') == 'true':
                print("第二個 API 請求成功！")
                record = data2.get('records',{})
                print(record," this is the record")
                element = record.get('weatherElement',{})
                print(element," this is the element")
                location = element.get('location',{})
                print(location," this is the location")
                uv_index = location[0]['UVIndex']
                print(uv_index," this is the UV")
                
            response_message = (
                                f"**{station_name}** 即時天氣資訊 ({obs_time}):\n"
                                f"🌡️ 溫度: {air_temperature}\n"
                                f"💧 濕度: {relative_humidity}\n"
                                f"💨 風速: {wind_speed}\n"
                                f"☀️ 紫外線指數: {uv_index}\n"
                            )
            await message.channel.send(response_message)
            
            content = message.content.replace(f"<@{self.bot.user.id}>", "")
            content = content.strip()
            content = content + f"現在外界氣溫{air_temperature}，現在濕度{relative_humidity}，現在風速{wind_speed}，最高紫外線{uv_index}"
            try:
                # 簡單的長度檢查，避免發送過長的問題給 API
                if len(content) > 200:
                    await message.channel.send("問題太長了，請簡短一些。")
                    return

                if not self.model: #
                    await message.channel.send("Gemini AI 服務未啟用，請檢查 API 金鑰。")
                    return

                if user_id not in self.user_chats:
                    # 如果是新用戶或該用戶的聊天會話尚未開始，則使用系統提示初始化一個新的聊天會話
                    print(f"為使用者 {user_id} 初始化新的 Gemini 聊天會話，載入系統提示。")
                    self.user_chats[user_id] = self.model.start_chat(history=self.SYSTEM_PROMPT_HISTORY)
                
                chat = self.user_chats[user_id] # 獲取該使用者的聊天會話物件
                response = chat.send_message(content)
                #response = self.model.generate_content(content) #

                # 檢查是否有內容並傳送回 Discord
                if response and response.text:
                    # Discord 訊息長度限制為 2000 字元
                    if len(response.text) > 2000:
                        await message.channel.send("答案太長了，將分段發送：")
                        # 將答案分割成多條訊息，每條不超過 1990 字元 (留一些空間給 ``` 和標點)
                        chunks = [response.text[i:i+1990] for i in range(0, len(response.text), 1990)]
                        for chunk in chunks:
                            await message.channel.send(f"```{chunk}```") # 使用 Markdown 程式碼區塊格式化
                    else:
                        await message.channel.send(f"```{response.text}```") # 使用 Markdown 程式碼區塊格式化

                    # 更新最後處理的訊息 ID，與使用者相關聯
                    self.bot.user_status[user_id]["last_message_id"] = message.id

                    print(f"[GeminiAI Cog] 回答成功發送：{response.text[:50]}...") # 日誌前50個字元
                    print(message.id, "message id" , self.bot.user_status[user_id]["last_message_id"]) #
                else:
                    await message.channel.send("Gemini 沒有生成有效的回答。")
                # 將 last_message_id 的更新移到這裡，確保無論成功或失敗都會更新，避免無限循環
                # self.bot.user_status[user_id]["last_message_id"] = message.id # 已經在上面更新過了，這裡不需要重複

            except Exception as e:
                print(f"[GeminiAI Cog] Error communicating with Gemini API: {e}")
                # 捕獲並回應錯誤訊息
                await message.channel.send(f"在與 Gemini 溝通時發生錯誤：`{e}`")
                await message.channel.send("請檢查您的問題或稍後再試。")
                
           
       

        

# Cog 檔案必須有一個 setup 函式
async def setup(bot):
    await bot.add_cog(Weather(bot))