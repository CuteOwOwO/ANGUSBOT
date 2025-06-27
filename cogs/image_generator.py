import os
import google.generativeai as genai
from google.generativeai import types # <--- 修正這裡的導入路徑
from io import BytesIO
import asyncio
import logging
from datetime import datetime

IMAGEN_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_KEY_2 = os.getenv('GEMINI_API_KEY_2') # 用於 Gemini 2.5 生成 Prompt



if GEMINI_API_KEY_2:
    genai.configure(api_key=GEMINI_API_KEY_2) # 設定 Gemini API 金鑰
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # 選擇一個快速的 Gemini 模型來生成Prompt
else:
    logging.error("GEMINI_API_KEY 未設定，無法使用 Gemini API。")
    gemini_model = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

specific_style_prompt = "A cute anime girl with long, flowing white hair, cat ears and tail, " \
                        "wearing a white dress with a black sailor-style collar and a black bow at the chest. " \
                        "She has amber eyes and a gentle expression. The overall style is soft and appealing, typical of anime illustrations."

async def generate_image_with_ai(conversation_history: str, image_name: str = "generated_image") -> BytesIO | None:
    """
    根據對話內容和指定風格，先由 Gemini 生成圖片 Prompt，再由 Imagen 生成圖片。
    圖片將以 BytesIO 物件的形式返回，不再儲存到磁碟。

    Args:
        conversation_history (str): 用戶與 AI 互動的相關對話內容，作為生圖場景和動作的參考。
        specific_style_prompt (str): 圖片的外觀和風格提示詞 (例如: "A cute anime girl with long, flowing white hair...")
        image_name (str): 圖片檔案的基礎名稱 (用於日誌或作為建議的 Discord 檔案名稱)。

    Returns:
        BytesIO | None: 成功生成圖片後的 BytesIO 物件，如果失敗則返回 None。
    """
    if not gemini_model :
        logging.error("AI 模型客戶端未正確初始化，無法生成圖片。請檢查 API Key 設定。")
        return None

    # 步驟 1: 使用 Gemini 根據對話內容生成 Imagen 的 Prompt
    try:
        logging.info("正在使用 Gemini 生成圖片提示詞 (Prompt)...")
        gemini_prompt_text = (
            f"以下是我們的對話內容：\n\n"
            f"\"\"\"{conversation_history}\"\"\"\n\n"
            f"請根據上述對話內容，並結合以下圖片外觀和風格提示詞，生成一個用於圖像生成模型（如 Imagen 3）的具體、詳細、且富有創意的英文提示詞 (Prompt)。這個提示詞應該描述一個包含以下元素，並具備以下風格的場景和動作：\n\n"
            f"圖片外觀和風格提示詞：\n"
            f"\"\"\"{specific_style_prompt}\"\"\"\n\n"
            f"請確保生成的提示詞能夠明確表達圖片的主題、人物動作、情緒、背景細節、光線氛圍等，並嚴格遵循指定的圖片外觀和風格。請直接給出提示詞，不要包含任何額外的說明性文字。"
            
        )
        
        response_parts = await gemini_model.generate_content_async(gemini_prompt_text)
        
        if hasattr(response_parts.candidates[0].content, 'parts') and response_parts.candidates[0].content.parts:
            imagen_prompt = response_parts.candidates[0].content.parts[0].text
        else:
            imagen_prompt = response_parts.text

        logging.info(f"Gemini 生成的圖片提示詞：\n{imagen_prompt}")
        imagen_prompt += "you dont have to show the diologue!!!!"  # 確保提示詞不包含對話內容
        if not imagen_prompt:
            logging.error("Gemini 未能生成有效的圖片提示詞。")
            return None

    except Exception as e:
        logging.error(f"使用 Gemini 生成圖片提示詞時發生錯誤: {e}")
        return None

    # 步驟 2: 使用 Imagen 根據生成的 Prompt 生成圖片
    try:
        logging.info("正在使用 Imagen 生成圖片...")
        imagen_response = await asyncio.to_thread(
            genai.models.generate_images,
            model='imagen-3.0-generate-002', # 請再次確認你的 Imagen 模型名稱
            prompt=imagen_prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1
            ),
        )

        if not imagen_response.generated_images:
            logging.warning("Imagen 未能生成任何圖片。")
            return None

        generated_image_data = imagen_response.generated_images[0].image.image_bytes
        
        # === 關鍵修改：將圖片位元組包裝成 BytesIO 物件並返回 ===
        image_stream = BytesIO(generated_image_data)
        image_stream.name = f"{image_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png" # 可選：給予一個建議的檔名
        logging.info(f"圖片已成功生成並包裝為 BytesIO 物件。")
        return image_stream

    except Exception as e:
        logging.error(f"使用 Imagen 生成圖片時發生錯誤: {e}")
        return None