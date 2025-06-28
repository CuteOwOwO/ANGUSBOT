import os
# === 🌟 針對 Gemini 模型的導入 (使用 google-generativeai 套件) 🌟 ===
import google.generativeai as gemini_genai # 給它一個別名 gemini_genai
from google.generativeai import types as gemini_types # 給它一個別名 gemini_types

# === 🌟 針對 Imagen 模型的導入 (基於你的 make_pictures.py，使用 google-genai 套件) 🌟 ===
from google import genai as imagen_genai # 給它一個別名 imagen_genai
from google.genai import types as imagen_types # 給它一個別名 imagen_types

from PIL import Image # 圖片處理庫
from io import BytesIO
import asyncio
import logging
from datetime import datetime
from typing import Union

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 從環境變數載入 API Keys
GEMINI_API_KEY_2 = os.getenv('GEMINI_API_KEY_2') # 這是你在 .env 裡設定的 Gemini API Key
IMAGEN_API_KEY = os.getenv('GEMINI_API_KEY') # 你的 make_pictures.py 裡 Imagen 用的是這個，請確保你的 .env 有設定

# ----------------------------------------------------
# 初始化 Gemini 模型
# ----------------------------------------------------
gemini_model = None
if GEMINI_API_KEY_2:
    gemini_genai.configure(api_key=GEMINI_API_KEY_2) # 用 gemini_genai 來配置
    gemini_model = gemini_genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    logging.error("GEMINI_API_KEY_2 未設定，無法使用 Gemini API。")

# ----------------------------------------------------
# 初始化 Imagen Client (根據你的 make_pictures.py)
# ----------------------------------------------------
imagen_client = None
if IMAGEN_API_KEY:
    try:
        # 使用從 google 導入的 genai 來創建 Client
        imagen_client = imagen_genai.Client(api_key=IMAGEN_API_KEY)
        logging.info("Imagen Client (從 google.genai 導入) 已成功初始化。")
    except Exception as e:
        logging.error(f"初始化 Imagen Client (從 google.genai 導入) 時發生錯誤: {e}")
        logging.error("請確認 'google-genai' 套件已正確安裝，並且 IMAGEN_API_KEY 有效。")
        imagen_client = None
else:
    logging.error("IMAGEN_API_KEY 未設定，無法初始化 Imagen Client。")
    
specific_style_prompt_loli = (
    "A cute little anime girl with long, flowing white hair, cat ears and tail, "
    "She has amber eyes and a gentle expression."
    "The overall style is soft and appealing, typical of anime illustrations."
)

specific_style_prompt_sexy = (
    "A sexy and pretty anime girl with long, flowing white hair, cat ears and tail, "
    "She has amber eyes and a gentle expression."
    "The overall style is soft and appealing, typical of anime illustrations."
)

outfit_prompt =  "she wears a white dress with a black sailor-style collar and a black bow at the chest."


async def generate_image_with_ai(conversation_history: str, mode: str, image_name: str = "generated_image") -> Union[BytesIO, None]:
    """
    根據對話內容和指定風格，先由 Gemini 生成圖片 Prompt，再由 Imagen 生成圖片。
    圖片將以 BytesIO 物件的形式返回。
    """
    # 檢查 Gemini 模型是否就緒
    if not gemini_model:
        logging.error("Gemini 模型未正確初始化，無法生成圖片提示詞。")
        return None
    
    # 檢查 Imagen Client 是否就緒
    if not imagen_client:
        logging.error("Imagen Client 未正確初始化，無法生成圖片。")
        return None

    # 步驟 1: 使用 Gemini 生成 Imagen 的 Prompt
    try:
        logging.info("正在使用 Gemini 生成圖片提示詞 (Prompt)...")
        specific_style_prompt = specific_style_prompt_loli if mode == "loli" else specific_style_prompt_sexy
        specific_style_prompt += " " + outfit_prompt  # 添加服裝提示詞
        gemini_prompt_text = (
            f"以下是我們的對話內容：\n\n"
            f"\"\"\"{conversation_history}\"\"\"\n\n"
            f"請根據上述對話內容，並結合以下圖片外觀和風格提示詞，生成一個用於圖像生成模型（如 Imagen 3）的具體、詳細、且富有創意的英文提示詞 (Prompt)。這個提示詞應該描述一個包含以下元素，並具備以下風格的場景和動作：\n\n"
            f"圖片外觀和風格提示詞：\n"
            f"\"\"\"{specific_style_prompt}\"\"\"\n\n"
            f"請確保生成的提示詞能夠明確表達圖片的主題、人物動作、情緒、背景細節、光線氛圍等，並嚴格遵循指定的圖片外觀和風格。請直接給出提示詞，不要包含任何額外的說明性文字。"
        )
        
        response_parts = await gemini_model.generate_content_async(gemini_prompt_text)
        
        # 提取 Gemini 回覆的文字內容
        if hasattr(response_parts.candidates[0].content, 'parts') and response_parts.candidates[0].content.parts:
            imagen_prompt = response_parts.candidates[0].content.parts[0].text
        else:
            imagen_prompt = response_parts.text

        logging.info(f"Gemini 生成的圖片提示詞：\n{imagen_prompt}")
        
        if not imagen_prompt:
            logging.error("Gemini 未能生成有效的圖片提示詞。")
            return None

    except Exception as e:
        logging.error(f"使用 Gemini 生成圖片提示詞時發生錯誤: {e}")
        return None

    # 步驟 2: 使用 Imagen Client 生成圖片 (完全複製 make_pictures.py 的邏輯)
    try:
        logging.info("正在使用 Imagen Client 生成圖片...")
        
        # 調用 Imagen Client 的 models.generate_images 方法
        imagen_response = await asyncio.to_thread(
            imagen_client.models.generate_images, # 使用 imagen_client.models
            model='imagen-3.0-generate-002',      # 指定模型
            prompt=imagen_prompt,
            config=imagen_types.GenerateImagesConfig( # 使用 imagen_types.GenerateImagesConfig
                number_of_images=1,
                #safety_filter_level="BLOCK_LOW_AND_ABOVE",
            ),
        )

        if not imagen_response.generated_images: # 檢查 .generated_images
            logging.warning("Imagen 未能生成任何圖片。")
            return None

        # 從回應中獲取圖片的位元組數據
        generated_image_data = imagen_response.generated_images[0].image.image_bytes
        
        image_stream = BytesIO(generated_image_data)
        image_stream.name = f"{image_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        logging.info(f"圖片已成功生成並包裝為 BytesIO 物件。")
        return image_stream

    except Exception as e:
        logging.error(f"使用 Imagen Client 生成圖片時發生錯誤: {e}")
        logging.error("可能的原因：API Key 權限不足、API 未啟用、或 Prompt 內容問題。")
        logging.error("請檢查您的 Google Cloud 專案設定和 API Key 相關配置。")
        return None