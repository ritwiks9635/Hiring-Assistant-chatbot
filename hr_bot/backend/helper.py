import os
import re
from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "api_key.env"))
api_keys = os.getenv('GOOGLE_API_KEY')

if not api_keys:
    raise ValueError("❌ Error: API key is missing! Please check api_key.env")

genai.configure(api_key=api_keys)

def greet_candidate():
    """
    Returns a greeting message to the candidate.
    """
    return (
        "Hello! Welcome to TalentScout's AI Hiring Assistant. "
        "I’ll guide you through the initial screening process. "
        "Let’s start by gathering some details about you."
    )



genai = genai.GenerativeModel(
    'gemini-1.5-flash-latest',
    generation_config=genai.GenerationConfig(
        max_output_tokens=200,
    ))


def generate_tech_questions(tech_stack, prev_questions=[]):
    """
    Generates technical interview questions one by one based on the given tech stack.
    Ensures questions are not blank.
    """

    prompt = f"""
    You are an AI Hiring Assistant. Generate only **one** technical question based on the following tech stack:

    Tech Stack: {tech_stack}

    Ensure the question tests practical skills, best practices, and problem-solving abilities.

    - Do not generate multiple questions, only one.
    - Make sure the question is **not blank**.
    - Do not repeat previous questions.
    - Format: **Only return the question text. Do not add extra text.**

    Previous Questions Asked: {prev_questions}
    """

    try:
        response = genai.generate_content([prompt])
        question = response.text.strip() if response else None

        # Retry if question is empty
        retry_count = 0
        while not question and retry_count < 3:
            response = genai.generate_content([prompt])
            question = response.text.strip() if response else None
            retry_count += 1

        if not question:
            return "⚠️ Error: Unable to generate a valid question at this time."


        return question
    except Exception as e:
        return f"Error generating question: {str(e)}"



def handle_unexpected_input():
    """
    Returns a response when the chatbot does not understand user input.
    """
    return "I'm sorry, I didn’t understand that. Could you please rephrase or provide more details?"


def validate_email(email):
    pattern = r"^[a-zA-Z0-9._+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def validate_phone(phone):
    pattern = r"^(\+91)?[6-9]\d{9}$"
    return bool(re.match(pattern, phone))



def exit_conversation():
    """
    Returns a polite exit message for candidates.
    """
    return (
        "Thank you for your time! TalentScout’s team will review your responses and reach out soon. "
        "Have a great day! 😊"
    )
