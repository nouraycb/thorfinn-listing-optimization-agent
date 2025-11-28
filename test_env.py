import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENAI_API_KEY")

print("API KEY FOUND:", bool(key))
print("API KEY VALUE:", key[:8] + "..." if key else "None")
