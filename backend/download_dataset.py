"""Try to download and unzip the official UCI dataset into backend/data/.
Run once:  python download_dataset.py
If it fails (no internet / UCI changed the link), follow the manual steps in README.md."""
import sys
import urllib.request
import zipfile
from pathlib import Path

from preprocess import DATA_DIR, RAW_FILE

URL = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
PAGE = "https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption"


def main():
    if RAW_FILE.exists():
        print("Dataset already present:", RAW_FILE)
        return 0
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / "dataset.zip"
    try:
        print("Downloading from", URL)
        urllib.request.urlretrieve(URL, zip_path)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(DATA_DIR)
        zip_path.unlink(missing_ok=True)
    except Exception as exc:  # network errors, bad zip, etc.
        print("\nAutomatic download failed:", exc)
        print("Download it manually from:", PAGE)
        print("Unzip it and place household_power_consumption.txt in:", DATA_DIR)
        return 1
    if not RAW_FILE.exists():
        print("Zip extracted but household_power_consumption.txt was not found in", DATA_DIR)
        return 1
    print("Done:", RAW_FILE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
