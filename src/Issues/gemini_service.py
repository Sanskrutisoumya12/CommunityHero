import os

from dotenv import load_dotenv

import google.generativeai as genai


load_dotenv()


genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)


model = genai.GenerativeModel(
    "gemini-2.5-flash"
)


def analyze_issue(description):

    prompt = f"""
    Analyze this civic issue.

    Description:
    {description}

    Return EXACTLY in this format:

    Category: <category>
    Priority: <low/medium/high>
    Summary: <short summary>
    """

    try:

        response = model.generate_content(
            prompt
        )

        return response.text

    except Exception as e:

        print(
            "GEMINI ERROR:",
            e
        )

        return """
Category: Infrastructure
Priority: Medium
Summary: AI analysis unavailable.
"""