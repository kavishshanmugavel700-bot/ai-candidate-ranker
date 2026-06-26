import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize the Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

try:
    print("Testing Groq API key...")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Hello! Please reply with a short confirmation message that you can hear me.",
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    print("API connection successful!")
    print("Response from Groq:")
    print(chat_completion.choices[0].message.content)
except Exception as e:
    print("API connection failed.")
    print("Error:", e)
