import os
import requests
from datetime import datetime
import ctypes
import logging
import winreg
import time  # برای sleep

# logging file path
log_file = os.path.join(os.path.expanduser("~"), "Pictures", "BingWallpapers", "bing_wallpaper.log")
logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# The list of resolutions to check for the best quality
RESOLUTIONS = ["7680x4320", "6016x3384", "UHD", "1920x1080"]

# Directory to save wallpapers
wallpaper_dir = os.path.join(os.path.expanduser("~"), "Pictures", "BingWallpapers")
os.makedirs(wallpaper_dir, exist_ok=True)

MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

attempt = 0
while attempt < MAX_RETRIES:
    try:
        # fetching the Bing wallpaper
        bing_url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
        response = requests.get(bing_url)
        response.raise_for_status()

        image_data = response.json()
        image_base_url = "https://www.bing.com" + image_data["images"][0]["url"]

        # finding the best resolution image
        best_url = None
        for res in RESOLUTIONS:
            test_url = image_base_url.replace("1920x1080", res)
            test_response = requests.head(test_url)
            if test_response.status_code == 200:
                best_url = test_url
                break

        if best_url:
            today = datetime.today().strftime('%Y-%m-%d')
            image_path = os.path.join(wallpaper_dir, f"bing_{today}_best.jpg")

            if not os.path.exists(image_path):
                img_data = requests.get(best_url).content
                with open(image_path, 'wb') as f:
                    f.write(img_data)

            # setting the wallpaper on Windows
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

            # updating registry for wallpaper style and tiling
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "6")
                winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")

            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

            print(f"✅ Wallpaper updated: {image_path} (Resolution: {best_url.split('_')[-1]})")
        else:
            print("❌ No high-resolution image found.")
            logging.error("No high-resolution image found.")

        break

    except Exception as e:
        attempt += 1
        logging.error(f"❌ Attempt {attempt} failed: {e}")
        if attempt < MAX_RETRIES:
            print(f"⚠️ Attempt {attempt} failed. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            print("❌ All attempts failed. Please check log for details.")
