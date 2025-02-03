import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
import cv2
import numpy as np
from io import BytesIO

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "7762588264:AAH5ovrQYzssK5Q8dDY4kWUUoZ2vSu8mHZA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! Send me a photo, and I will analyze its color correction. I will also provide Lightroom adjustment recommendations."
    )

async def analyze_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        photo_file = await update.message.photo[-1].get_file()
        img_data = await photo_file.download_as_bytearray()
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR) 

        analysis = analyze_colors(img)
        response = format_analysis(analysis)
        lightroom_recommendations = generate_lightroom_tips(analysis)

        corrected_img = apply_corrections(img, analysis)
        corrected_img_bytes = cv2.imencode(".jpg", corrected_img)[1].tobytes()
        bio = BytesIO(corrected_img_bytes)
        bio.name = "corrected_photo.jpg"

        full_response = f"{response}\n\n💡 Lightroom Recommendations:\n{lightroom_recommendations}"

        await update.message.reply_text(full_response)
        await update.message.reply_document(
            document=bio,
            caption="🖼️ Here is the processed photo. Download it!",
            filename="corrected_photo.jpg"
        )

    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ Something went wrong. Try another photo.")

def analyze_colors(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    mean_hue = np.mean(hsv[:, :, 0])
    mean_saturation = np.mean(hsv[:, :, 1])
    mean_value = np.mean(hsv[:, :, 2])
    
    analysis = {
        "brightness": "Low" if mean_value < 100 else "High" if mean_value > 150 else "Normal",
        "saturation": "Low" if mean_saturation < 40 else "High" if mean_saturation > 200 else "Normal",
        "hue_balance": "Shifted to warm tones" if mean_hue < 15 or mean_hue > 165 else "Shifted to cool tones" if 75 < mean_hue < 135 else "Balanced"
    }
    return analysis

def format_analysis(analysis):
    tips = []
    if analysis["brightness"] != "Normal":
        tips.append(f"🔅 Brightness: {analysis['brightness']}. Tip: {'increase brightness' if analysis['brightness'] == 'Low' else 'decrease brightness'}.")
    if analysis["saturation"] != "Normal":
        tips.append(f"🎨 Saturation: {analysis['saturation']}. Tip: {'increase saturation' if analysis['saturation'] == 'Low' else 'decrease saturation'}.")
    if "Shifted" in analysis["hue_balance"]:
        tips.append(f"🌈 Color balance: {analysis['hue_balance']}. Tip: adjust the white balance.")
    
    if not tips:
        return "✅ The photo looks good! There are no significant color correction issues."
    return "\n".join(["📸 Analysis results:"] + tips)

def generate_lightroom_tips(analysis):
    tips = []
    if analysis["brightness"] == "Low":
        tips.append("Increase Exposure by +0.3 to +0.7 in the Basic Panel.")
    elif analysis["brightness"] == "High":
        tips.append("Decrease Exposure by -0.3 to -0.7 in the Basic Panel.")
    
    if analysis["saturation"] == "Low":
        tips.append("Increase Vibrance by +10 to +25, and Saturation slightly.")
    elif analysis["saturation"] == "High":
        tips.append("Decrease Vibrance by -10 to -25 to reduce oversaturation.")
    
    if "Shifted to warm tones" in analysis["hue_balance"]:
        tips.append("Adjust Temperature slider slightly towards the cooler side (-5 to -15).")
    elif "Shifted to cool tones" in analysis["hue_balance"]:
        tips.append("Adjust Temperature slider slightly towards the warmer side (+5 to +15).")
    
    if not tips:
        return "✅ The photo is well-balanced. No Lightroom adjustments needed."
    return "\n".join(tips)

def apply_corrections(img, analysis):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    
    if analysis["brightness"] == "Low":
        hsv[:, :, 2] *= 1.3
    elif analysis["brightness"] == "High":
        hsv[:, :, 2] *= 0.8

    if analysis["saturation"] == "Low":
        hsv[:, :, 1] *= 1.4
    elif analysis["saturation"] == "High":
        hsv[:, :, 1] *= 0.7

    hsv = np.clip(hsv, 0, 255)
    corrected_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    return corrected_img

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_photo))
    
    app.run_polling()

if __name__ == "__main__":
    main()
