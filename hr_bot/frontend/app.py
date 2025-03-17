from dotenv import load_dotenv
import streamlit as st
import google.generativeai as genai
import csv
import os
import sys

# Importing helper functions
from backend.helper import (
    greet_candidate,
    generate_tech_questions,
    handle_unexpected_input,
    exit_conversation,
    validate_email,
    validate_phone
)

# Set up Gemini API
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "api_key.env"))
api_keys = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=api_keys)
genai = genai.GenerativeModel('gemini-1.5-flash-latest')

# Initialize session state
if "step" not in st.session_state:
    st.session_state.step = "greeting"
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "candidate_data" not in st.session_state:
    st.session_state.candidate_data = {}
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "question_answers" not in st.session_state:
    st.session_state.question_answers = {}



# Function to save data in CSV
def save_data_to_csv():
    file_path = os.path.join(os.path.dirname(__file__), "..", "backend", "save_user_information", "candidate_responses.csv")
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    fieldnames = ["Name", "Email", "Phone", "Experience", "Position", "Location", "Tech Stack", "Question", "Answer", "Correct"]

    file_exists = os.path.isfile(file_path)

    with open(file_path, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for question, answer_data in st.session_state.question_answers.items():
            writer.writerow({
                "Name": st.session_state.candidate_data["name"],
                "Email": st.session_state.candidate_data["email"],
                "Phone": st.session_state.candidate_data["phone"],
                "Experience": st.session_state.candidate_data["experience"],
                "Position": st.session_state.candidate_data["position"],
                "Location": st.session_state.candidate_data["location"],
                "Tech Stack": st.session_state.candidate_data["tech_stack"],
                "Question": question,
                "Answer": answer_data["answer"],
                "Correct": answer_data["correct"]
            })

# Streamlit UI
st.markdown("<h1 style='text-align: center; color: #2E3B4E;'>🤖 TalentScout AI Hiring Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Welcome! I will guide you through the initial screening process.</p>", unsafe_allow_html=True)
st.divider()

# Step 1: Greeting
if st.session_state.step == "greeting":
    st.write(greet_candidate())
    if st.button("🚀 Start Interview"):
        st.session_state.step = "collect_info"
        st.rerun()

# Step 2: Collect Candidate Information
elif st.session_state.step == "collect_info":
    st.subheader("📌 Candidate Information")

    name = st.text_input("Full Name", value=st.session_state.candidate_data.get("name", ""))
    email = st.text_input("Email Address", value=st.session_state.candidate_data.get("email", ""))
    phone = st.text_input("Phone Number", value=st.session_state.candidate_data.get("phone", ""))
    experience = st.number_input("Years of Experience", min_value=0, max_value=50, step=1, value=st.session_state.candidate_data.get("experience", 0))
    position = st.text_input("Desired Position(s)", value=st.session_state.candidate_data.get("position", ""))
    location = st.text_input("Current Location", value=st.session_state.candidate_data.get("location", ""))
    tech_stack = st.text_area("Tech Stack (Programming Languages, Frameworks, Databases, Tools)", value=st.session_state.candidate_data.get("tech_stack", ""))

    if st.button("Submit Information"):
        if not name.strip():
            st.error("❌ Please enter your name.")
        elif not validate_email(email):
            st.error("❌ Invalid Email Format. Please enter a valid email.")
        elif not validate_phone(phone):
            st.error("❌ Invalid Phone Number. Please enter a valid phone number.")
        elif not tech_stack.strip():
            st.error("❌ Please enter at least one technology in Tech Stack.")
        else:
            st.session_state.candidate_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "experience": experience,
                "position": position,
                "location": location,
                "tech_stack": tech_stack
            }
            st.session_state.step = "generate_questions"
            st.rerun()

# Step 3: Generate Technical Questions
elif st.session_state.step == "generate_questions":
    st.subheader("🛠️ Technical Assessment")

    tech_stack = st.session_state.candidate_data["tech_stack"]
    st.write(f"🔍 Generating questions for: **{tech_stack}**...")

    if not st.session_state.questions:
        st.session_state.questions = generate_tech_questions(tech_stack).split("\n")

    st.session_state.step = "ask_questions"
    st.rerun()

# Step 4: Ask Questions One by One with Skip Button
elif st.session_state.step == "ask_questions":
    st.subheader("📝 Answer the Questions")

    index = st.session_state.current_question_index

    if index < len(st.session_state.questions):
        question = st.session_state.questions[index]
        st.write(f"**Q{index+1}:** {question}")

        answer = st.text_area("Your Answer", key=f"answer_{index}")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.button("✔️ Submit Answer")
        with col2:
            skip = st.button("⏩ Skip Question")

        if submit:
            validation_prompt = f"""
            Check if the answer is **correct and relevant**:

            Question: {question}
            Answer: {answer}

            - If the answer is correct, return: **"Correct"**
            - If the answer is incorrect, return: **"Incorrect"**
            - If the answer is **unrelated to the question**, return: **"Unclear response"**
            """

            validation_response = genai.generate_content(validation_prompt).text

            if "Correct" in validation_response:
                is_correct = "Yes"
            elif "Incorrect" in validation_response:
                is_correct = "No"
            else:
                is_correct = handle_unexpected_input()
                st.error("⚠️ Please rephrase or provide a relevant answer.")

            st.session_state.question_answers[question] = {"answer": answer, "correct": is_correct}

            if is_correct != handle_unexpected_input():
                st.session_state.current_question_index += 1

        elif skip:
            st.session_state.current_question_index += 1

        if st.session_state.current_question_index >= len(st.session_state.questions):
            st.session_state.step = "completed"

        st.rerun()

    else:
        st.session_state.step = "completed"
        st.rerun()

# Step 5: Exit & Save
elif st.session_state.step == "completed":
    st.success("✅ Interview Process Completed!")

    save_data_to_csv()
    st.write(exit_conversation())

    st.session_state.step = "exit"
    st.stop()
