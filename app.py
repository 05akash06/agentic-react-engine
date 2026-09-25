import os
import json
import streamlit as st # type: ignore
from dotenv import load_dotenv # type: ignore

try:
    from ddgs import DDGS # type: ignore
except ImportError:
    from duckduckgo_search import DDGS # type: ignore

from groq import Groq # type: ignore

# Load environment variables from .env
load_dotenv()

# --- Tool Definitions ---
def web_search(query: str) -> str:
    """Searches DuckDuckGo for up-to-date web information."""
    try:
        results = list(DDGS().text(query, max_results=3))
        return json.dumps(results)
    except Exception as e:
        return f"Search error: {str(e)}"

def calculate(expression: str) -> str:
    """Evaluates a mathematical expression safely."""
    try:
        allowed = "0123456789+-*/(). "
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "Invalid math expression."
    except Exception as e:
        return f"Calculation error: {str(e)}"

def save_to_file(content: str) -> str:
    """Saves text content to a markdown file."""
    try:
        filename = "agent_output.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully saved to {filename}"
    except Exception as e:
        return f"File save error: {str(e)}"

tools = {
    "web_search": web_search,
    "calculate": calculate,
    "save_to_file": save_to_file
}

# --- System Prompt ---
SYSTEM_PROMPT = """
You are an AI Agentic Assistant.
You achieve goals by breaking tasks into steps, using tools, and reasoning about results.

Available Tools:
1. web_search(query: str): Search web for real information.
2. calculate(expression: str): Solve math problems.
3. save_to_file(content: str): Save final plan or results to a file.

Output Format:
RESPOND WITH JSON ONLY. NO OTHER TEXT. Keep your 'thought' field brief (under 2 sentences).
You MUST respond in JSON object format strictly:
{
    "thought": "Brief step-by-step reasoning",
    "action": "web_search" OR "calculate" OR "save_to_file" OR "final_answer",
    "action_input": "parameter for tool or final response text"
}
"""

def get_active_model(client: Groq) -> str:
    """Prioritizes standard Llama/Qwen models to bypass native function call auto-intercept errors."""
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data]
        
        preferred = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "qwen-2.5-32b"
        ]
        
        for pref in preferred:
            if pref in model_ids:
                return pref
                
        filtered = [
            m_id for m_id in model_ids 
            if not any(blocked in m_id for blocked in ["orpheus", "whisper", "allam", "guard", "gpt-oss"])
        ]
        
        if filtered:
            return filtered[0]
            
    except Exception as e:
        pass
        
    return "llama-3.1-8b-instant"

# --- Streamlit Web Application ---
st.set_page_config(page_title="AI Agentic System", page_icon="🤖")
st.title("🤖 Custom ReAct AI Agent Execution Engine")

user_task = st.text_input(
    "Enter your task:", 
    "Plan a 3-day trip to Tokyo with a $1500 budget. Search real travel costs and calculate average daily budget."
)

if st.button("Run Agent"):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("GROQ_API_KEY missing in .env file!")
    else:
        client = Groq(api_key=api_key)
        selected_model = get_active_model(client)
        st.info(f"Active Model Running: `{selected_model}`")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Task: {user_task}"}
        ]

        step = 1
        max_steps = 6

        while step <= max_steps:
            with st.expander(f"Step {step}", expanded=True):
                try:
                    response = client.chat.completions.create(
                        model=selected_model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.2,
                        max_tokens=800,
                        extra_body={"disable_tool_validation": True}
                    )
                except Exception as e:
                    st.error(f"API Error: {e}")
                    break

                raw_content = response.choices[0].message.content
                
                try:
                    output = json.loads(raw_content)
                except json.JSONDecodeError as e:
                    st.error(f"JSON Parsing Error: {e}")
                    st.code(raw_content)
                    break

                if isinstance(output, list) and len(output) > 0:
                    output = output[0]

                thought = output.get("thought", "Reasoning...")
                action = output.get("action", "")
                action_input = output.get("action_input", "")

                st.markdown(f"**🧠 Thought:** {thought}")

                if action == "final_answer":
                    st.success("✅ **Final Response:**")
                    st.write(action_input)
                    break

                if action in tools:
                    st.markdown(f"**🛠️ Executing Tool:** `{action}` | **Input:** `{action_input}`")
                    tool_result = tools[action](action_input)
                    st.text_area("👁️ Observation", tool_result, height=100)

                    messages.append({"role": "assistant", "content": json.dumps(output)})
                    messages.append({"role": "user", "content": f"Observation from {action}: {tool_result}"})
                else:
                    st.warning("⚠️ Unknown or missing action.")

                step += 1