from dotenv import load_dotenv
import os

load_dotenv()
url = os.getenv("POSTGRES_URL")
print(f"POSTGRES_URL exists: {url is not None}")
if url:
    print(f"Length: {len(url)}")
    print(f"First 60 chars: {url[:60]}")
    print(f"Last 30 chars: {url[-30:]}")
    print(f'Contains password separator (:): {url.count(":")}')
else:
    print("ERROR: POSTGRES_URL not found in environment!")
