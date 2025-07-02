import os
# === 🌟 針對 Gemini 模型的導入 (使用 google-generativeai 套件) 🌟 ===
import google.generativeai as gemini_genai # 給它一個別名 gemini_genai
from google.generativeai import types as gemini_types # 給它一個別名 gemini_types

# === 🌟 針對 Gradio Client 的導入 🌟 ===
from gradio_client import Client # 導入 Gradio Client
# from gradio_client import utils # utils 如果沒有用到可以不導入，精簡程式碼

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

# === 🌟 新增：載入 Hugging Face API Key 🌟 ===
HF_TOKEN = os.getenv("ANYTHING_API_KEY") # 從環境變數讀取 HF Token

# ----------------------------------------------------
# 初始化 Gemini 模型
# ----------------------------------------------------
gemini_model = None
if GEMINI_API_KEY_2:
    gemini_genai.configure(api_key=GEMINI_API_KEY_2) # 用 gemini_genai 來配置
    gemini_model = gemini_genai.GenerativeModel('gemini-1.5-flash-latest')
    logging.info("Gemini 模型已成功初始化。")
else:
    logging.error("GEMINI_API_KEY_2 未設定，無法使用 Gemini API。")


gradio_client_instance = None
GRADIO_SPACE_ID = "Asahina2K/animagine-xl-4.0"

if HF_TOKEN:
    try:
        gradio_client_instance = Client(GRADIO_SPACE_ID, hf_token=HF_TOKEN)
        logging.info(f"Gradio Client 已成功初始化並連接到 Space: {GRADIO_SPACE_ID}")
        # 如果需要，可以在這裡打印 client.view_api() 來查看該 Space 的 API 簽名
        # logging.info(gradio_client_instance.view_api())
    except Exception as e:
        logging.error(f"初始化 Gradio Client 時發生錯誤：{e}")
        logging.error("請確認 'gradio_client' 套件已正確安裝，並且 HUGGING_FACE_API_KEY 有效。")
        gradio_client_instance = None
else:
    logging.error("HUGGING_FACE_API_KEY 未設定，無法初始化 Gradio Client。")


# 預設的風格提示詞和服裝提示詞
specific_style_prompt_loli = (
    "A cute little anime girl with long, flowing white hair, cat ears and tail, "
    "She has amber eyes and a gentle expression."
    
    "Anime style, close-up shot, detailed textures, soft lighting"
    "The scene is soft, warm, and inviting, with gentle sunlight illuminating the scene, emphasizing her soft white hair and dress"
    "soft scene , anime style, detailed textures, soft lighting"
    "the scene should contain  the whole face so that ear is visible"
)

specific_style_prompt_sexy = (
    "A sexy and pretty anime girl with long, flowing white hair, cat ears and tail, "
    "She has amber eyes and a gentle expression."
    "She wears sexily emphasizing her curves and femininity."
    "She is with big boobs"
    "Anime style, close-up shot, detailed textures, soft lighting"
    "The scene is soft, warm, and inviting, with gentle sunlight illuminating the scene, emphasizing her soft white hair and dress"
    "soft scene , anime style, detailed textures, soft lighting"
    "the scene should contain  the whole face so that ear is visible"
)



outfit_prompt = "she wears a white dress with a black sailor-style collar and a black bow at the chest."


async def generate_image_with_ai(conversation_history: str, mode: str, way : str , image_name: str = "generated_image") -> Union[BytesIO, None]:
    """
    根據對話內容和指定風格，先由 Gemini 生成圖片 Prompt，再由 Hugging Face Gradio Client 生成圖片。
    圖片將以 BytesIO 物件的形式返回。
    """
    # 檢查 Gemini 模型是否就緒
    if not gemini_model:
        logging.error("Gemini 模型未正確初始化，無法生成圖片提示詞。")
        return None
    
    # 檢查 Gradio Client 是否就緒
    if not gradio_client_instance:
        logging.error("Gradio Client 未正確初始化，無法生成圖片。")
        return None

    # 步驟 1: 使用 Gemini 生成 Gradio 模型的 Prompt
    try:
        logging.info("正在使用 Gemini 生成圖片提示詞 (Prompt)...")
        specific_style_prompt = specific_style_prompt_loli if mode == "loli" else specific_style_prompt_sexy
        specific_style_prompt += " " + outfit_prompt  # 添加服裝提示詞

        # 為 Gradio 模型的 prompt 準備更詳細的指令
        gemini_prompt_text = (
            "你要生成的是一位擬人的可愛貓娘以及用戶之間的對話，"
            f"以下是我們的對話內容，請將其轉換為好看的畫面，不用完全呈現對話內容：\n\n"
            f"\"\"\"{conversation_history}\"\"\"\n\n"
            f"請根據上述對話內容，並結合以下圖片外觀和風格提示詞，生成一個用於圖像生成模型（例如 Animagine XL 4.0）的具體、詳細、且富有創意的英文提示詞 (Prompt)。這個提示詞應該描述一個包含以下元素，並具備以下風格的場景和動作："
            f"圖片外觀和風格提示詞：\n"
            f"\"\"\"{specific_style_prompt}\"\"\"\n\n"
            f"請確保生成的提示詞能夠明確表達圖片的主題、人物動作、情緒、背景細節、光線氛圍等。請直接給出提示詞，不要包含任何額外的說明性文字。"
            "生成**英文的、逗號分隔的、適用於二次元美少女風格圖片生成模型（如Stable Diffusion）的關鍵詞列表（tags）**。"
            "請確保提示詞包含人物、服裝、場景、表情、動作和氛圍的詳細細節，**並以高質量繪圖常見的關鍵詞開頭**（例如'masterpiece, best quality, highly detailed'）。**不要使用完整的句子，只提供關鍵詞和短語。**"
        )
        
        if way != "command" :
            response_parts = await gemini_model.generate_content_async(gemini_prompt_text)
        
        if way == "command" : 
            '''if mode == "loli" :
                gradio_model_prompt = "1girl , young , masterpiece, best quality, highly detailed" + \
                "a cute girl , cat ears and tail, cat , cat "
                " anime style, cute anime , cute " + \
                " long white hair, flowing hair, amber eyes, gentle expression, cute, soft lighting, warm lighting, sunlight, close-up, detailed textures, white dress, black sailor collar, black bow, soft scene"
            if mode == "sexy" :
                gradio_model_prompt = "1girl , masterpiece, best quality, highly detailed" + \
                "a sexy girl , cat ears and tail, " + \
                " anime style, sexy anime , beautiful " + \
                " long white hair, flowing hair, amber eyes, gentle expression, sexy, soft lighting, warm lighting, sunlight, close-up, detailed textures, white dress, black sailor collar, black bow, soft scene"
            gradio_model_prompt += conversation_history
            gradio_model_prompt += " long white hair , cat ears and tail , whole face so that ear is visible" # <--- 這裡加上了 "cat ears and tail , cat ears and tail , whole face so that ear is visible"'''
            response_parts = await gemini_model.generate_content_async(gemini_prompt_text)
        # 檢查 Gemini 回覆是否包含內容
        
        # 提取 Gemini 回覆的文字內容
        
        if hasattr(response_parts.candidates[0].content, 'parts') and response_parts.candidates[0].content.parts:
            gradio_model_prompt = response_parts.candidates[0].content.parts[0].text
        else:
            gradio_model_prompt = response_parts.text
    
        logging.info(f"Gemini 生成的圖片提示詞：\n{gradio_model_prompt}")
        
        
        if not gradio_model_prompt:
            logging.error("Gemini 未能生成有效的圖片提示詞。")
            return None

    except Exception as e:
        logging.error(f"使用 Gemini 生成圖片提示詞時發生錯誤: {e}")
        return None

    # 步驟 2: 使用 Gradio Client 生成圖片 (結合你朋友的成功經驗)
    try:
        logging.info(f"正在使用 Gradio Client ({GRADIO_SPACE_ID}) 生成圖片...")

        # 結合 Gemini 生成的提示詞和固定品質標籤
        
        final_gradio_prompt = f"{gradio_model_prompt}, masterpiece, high score, great score, absurdres"
        
        if way == "command" :
            final_gradio_prompt += " , " + conversation_history # <--- 這裡加上了對話歷史
        final_gradio_prompt += "whole face , ears visibale , cat ears , whole face , whole face so that ear is visible" # <--- 這裡加上了 "cat ears and tail , whole face so that ear is visible"
        final_gradio_prompt = final_gradio_prompt.strip() # <--- 加上這行！
        logging.info(f"最終 Prompt 的長度：{len(final_gradio_prompt)}")
        logging.info(f"最終 Prompt 的 repr (顯示不可見字元): {repr(final_gradio_prompt)}") # <--- 新增這行！
        
        # 固定負面提示詞 (從你朋友的程式碼複製)
        gradio_negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, fewer digits, cropped, worst quality, low quality, low score, bad score, average score, signature, watermark, username, blurry"

        # Gradio 應用程式的固定參數 (從你朋友的程式碼複製)
        # 這些參數的順序和含義必須嚴格按照 Gradio 應用程式的 /generate 函數定義
        seed = 0
        custom_width = 1024
        custom_height = 1024
        guidance_scale = 7.5
        num_inference_steps = 50
        sampler = 'Euler a'
        aspect_ratio_selector = 'Custom'
        style_selector = '(None)'
        use_upscaler = False
        upscaler_strength = 0.55
        upscale_by = 1.5
        add_quality_tags = True
        api_name = "/generate" # 這個是關鍵，指定要調用 Gradio 應用的哪個內部函數
        
        # 在單獨的線程中運行同步的 client.predict() 函數
        result = await asyncio.wait_for(
            asyncio.to_thread(gradio_client_instance.predict,
                final_gradio_prompt,       # 1. prompt
                gradio_negative_prompt,    # 2. negative_prompt
                seed,                      # 3. seed
                custom_width,              # 4. custom_width
                custom_height,             # 5. custom_height
                guidance_scale,            # 6. guidance_scale
                num_inference_steps,       # 7. num_inference_steps
                sampler,                   # 8. sampler
                aspect_ratio_selector,     # 9. aspect_ratio_selector
                style_selector,            # 10. style_selector
                use_upscaler,              # 11. use_upscaler
                upscaler_strength,         # 12. upscaler_strength
                upscale_by,                # 13. upscale_by
                add_quality_tags,          # 14. add_quality_tags
                api_name=api_name          # api_name
            ),
            timeout=300 # 5分鐘超時
        )

        # 根據你朋友程式碼的經驗，結果是一個 tuple，第一個元素是圖片列表
        generated_images_list = result[0] 

        if generated_images_list and len(generated_images_list) > 0 and 'image' in generated_images_list[0]:
            # Gradio Client 在 predict 成功後會將圖片下載到本地臨時文件
            image_path_from_client = generated_images_list[0]['image']
            logging.info(f"圖片已在 Gradio Space 生成，並下載到臨時路徑: {image_path_from_client}")

            if isinstance(image_path_from_client, str) and os.path.exists(image_path_from_client):
                with open(image_path_from_client, 'rb') as f:
                    image_bytes = f.read()
                os.remove(image_path_from_client) # 清理臨時文件
            else:
                raise ValueError(f"Gradio Client 返回的圖片數據格式無法識別或檔案不存在: {image_path_from_client}")

            image_stream = BytesIO(image_bytes)
            image_stream.name = f"{image_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            logging.info(f"圖片已成功生成並包裝為 BytesIO 物件。")
            return image_stream

        else:
            logging.warning("Gradio Client 未能返回有效的圖片數據列表。")
            logging.warning(f"完整結果: {result}")
            return None

    except asyncio.TimeoutError:
        logging.error("Gradio Client 請求超時。Hugging Face Space 可能太忙或任務太複雜。")
        return None
    except Exception as e:
        logging.error(f"使用 Gradio Client 生成圖片時發生錯誤：{type(e).__name__}: {e}")
        logging.error("可能的原因：Hugging Face Space 不可用、HF Token 權限不足、或參數不匹配。")
        return None