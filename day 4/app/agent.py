import os

from dotenv import load_dotenv
from google import genai

from app.tools.course_tool import get_course_information
from app.tools.resource_tool import search_study_resources


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )


client = genai.Client(api_key=API_KEY)


SYSTEM_INSTRUCTION = """
You are the Supervisor Agent for a College Academic Assistant.

Your job is to understand the user's academic question and select
the correct tool when repository information is required.

Available tools:

1. get_course_information
Use this for:
- course details
- course code
- credits
- prerequisites
- course description

2. search_study_resources
Use this for:
- tutorials
- documentation
- courses
- study materials
- learning resources
- books
- learning websites

Rules:
- Select the appropriate tool based on the user's question.
- Do not invent academic information.
- Use the repository when the requested information is stored there.
- After receiving the tool result, give the user a concise answer.
- If information is not found, clearly say that it was not found.
"""


def ask_agent(user_query: str) -> str:

    chat = client.chats.create(
        model="gemini-3.6-flash",
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": [
                get_course_information,
                search_study_resources
            ]
        }
    )

    response = chat.send_message(user_query)

    return response.text