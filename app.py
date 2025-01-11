import streamlit as st
from PIL import Image
import os
import pandas as pd
import random
import time
import aiohttp
import asyncio

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

async def perform_ocr(image_path: str) -> str:
    """Perform OCR recognition using OpenRouter's OpenAI-compatible API."""
    BASE_URL = "https://openrouter.ai/api/v1"
    OCR_API_KEY = "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"
    MODEL = "anthropic/claude-3-haiku"

    headers = {
        "Authorization": f"Bearer {OCR_API_KEY}",
        "Content-Type": "application/json",
    }

    with open(image_path, "rb") as img_file:
        image_data = img_file.read()

    body = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an OCR processing assistant.",
            },
            {
                "role": "user",
                "content": f"Please extract text from this image.",
                "files": [
                    {
                        "name": os.path.basename(image_path),
                        "type": "image/jpeg",
                        "data": image_data.decode('latin1'),
                    }
                ],
            },
        ],
    }

    url = f"{BASE_URL}/chat/completions"

    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(url, json=body, headers=headers, timeout=60) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        raise ValueError(f"Error from OCR API: {response_data.get('error', 'Unknown error')}")

                    return response_data["choices"][0]["message"]["content"]
            except aiohttp.ClientError as e:
                if attempt < 2:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    raise RuntimeError("OCR failed after 3 attempts") from e


def spelling_accuracy(extracted_text):
    corrected_text = extracted_text[::-1]  # Placeholder for correction logic
    return ((len(extracted_text) - levenshtein(extracted_text, corrected_text)) / (len(extracted_text) + 1)) * 100

def gramatical_accuracy(extracted_text):
    corrected_text = extracted_text[::-1]  # Placeholder for correction logic
    return ((len(corrected_text) - levenshtein(extracted_text, corrected_text)) / (len(corrected_text) + 1)) * 100

def percentage_of_corrections(extracted_text):
    corrections = len(extracted_text.split()) // 2  # Placeholder
    return (corrections / len(extracted_text.split())) * 100

def percentage_of_phonetic_accuraccy(extracted_text):
    score = len(extracted_text) % 100  # Placeholder logic
    return score

def get_feature_array(extracted_text: str):
    feature_array = []
    feature_array.append(spelling_accuracy(extracted_text))
    feature_array.append(gramatical_accuracy(extracted_text))
    feature_array.append(percentage_of_corrections(extracted_text))
    feature_array.append(percentage_of_phonetic_accuraccy(extracted_text))
    return feature_array

def score(input):
    if input[0] <= 96.40350723266602:
        var0 = [0.0, 1.0]
    else:
        if input[1] <= 99.1046028137207:
            var0 = [0.0, 1.0]
        else:
            if input[2] <= 2.408450722694397:
                if input[2] <= 1.7936508059501648:
                    var0 = [1.0, 0.0]
                else:
                    var0 = [0.0, 1.0]
            else:
                var0 = [1.0, 0.0]
    return var0

st.set_page_config(page_title="Dyslexia Handwriting Detection")
st.header("Dyslexia Detection Using Handwriting Samples")
st.write("This application predicts the presence of dyslexia based on handwriting samples.")

image = st.file_uploader("Upload a handwriting sample", type=["jpg", "png", "jpeg"])
if image is not None:
    st.write("Please review the uploaded image.")
    st.image(image, width=224)
    image_path = f"temp_{random.randint(1000,9999)}.jpg"
    with open(image_path, "wb") as f:
        f.write(image.getbuffer())

    if st.button("Predict"):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            extracted_text = loop.run_until_complete(perform_ocr(image_path))
            feature_array = get_feature_array(extracted_text)
            result = score(feature_array)
            if result[0] == 1:
                st.write("✅ The handwriting sample indicates a very slim chance of dyslexia.")
            else:
                st.write("⚠️ The handwriting sample indicates a high likelihood of dyslexia.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            os.remove(image_path)
