import os
import tempfile
import streamlit as st
from google import genai
import git

# Set page configuration for a clean layout
st.set_page_config(
    page_title="AI Codebase Auditor", page_icon="🤖", layout="wide"
)

st.title("🤖 Context-Aware AI Codebase Auditor & Refactoring Assistant")
st.markdown(
    "Enter a public GitHub repository link below to automatically clone, scan,"
    " and audit its code files using Google Gemini."
)

# Securely load the API key from environment variables or Streamlit secrets
api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")

# Input fields for the user
repo_url = st.text_input(
    "Enter Public GitHub Repository URL:",
    "https://github.com/octocat/Spoon-Knife",
)

max_files = st.slider(
    "Maximum files to audit at once:", min_value=1, max_value=5, value=3
)

if st.button("Audit Repository", type="primary"):
  if not api_key:
    st.error(
        "Gemini API key not found! Please set GEMINI_API_KEY in your environment"
        " or Streamlit secrets."
    )
  elif not repo_url.strip():
    st.warning("Please enter a valid GitHub repository URL!")
  else:
    with st.spinner("Cloning repository and scanning files..."):
      # 1. Create a safe temporary directory to hold the downloaded repo
      with tempfile.TemporaryDirectory() as temp_dir:
        try:
          # Download the repository (depth=1 makes it fast)
          git.Repo.clone_from(repo_url, temp_dir, depth=1)
          st.success("Repository downloaded successfully!")

          # 2. Search through the folder for code files
          code_files = []
          for root, dirs, files in os.walk(temp_dir):
            # Skip hidden folders like .git
            if ".git" in root:
              continue
            for file in files:
              if file.endswith((".py", ".js", ".ts", ".html", ".cpp")):
                code_files.append(os.path.join(root, file))

          st.info(f"Found {len(code_files)} code files in the repository.")

          if not code_files:
            st.warning("No supported code files found in this repository.")
          else:
            # 3. Initialize Gemini client
            client = genai.Client(api_key=api_key)

            # 4. Loop through and audit the files up to the user's limit
            for file_path in code_files[:max_files]:
              relative_path = os.path.relpath(file_path, temp_dir)
              st.markdown(f"--- \n### 📁 File: `{relative_path}`")

              # Read the contents of the file
              with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code_content = f.read()

              if code_content.strip():
                with st.spinner(f"Analyzing {relative_path} with Gemini..."):
                  # Send code to Gemini for review and refactoring suggestions
                  response = client.models.generate_content(
                      model="gemini-3.5-flash",
                      contents=(
                          "Review this code file, find any bugs, security"
                          " issues, or code smells, and provide a clean"
                          " refactored version with explanations:\n\n"
                          f"{code_content}"
                      ),
                  )
                  st.markdown(response.text)
              else:
                st.info(f"File `{relative_path}` is empty.")

        except Exception as e:
          st.error(f"Something went wrong: {e}")
