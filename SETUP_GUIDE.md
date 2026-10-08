# Newsletter prototype setup

Run the newsletter app locally on Windows or macOS. No paid AI account or API key is needed. Internet is needed for installation and collecting articles; Qwen runs on your computer.

## 1. Install the tools

- Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/). On Windows, select **Add Python to PATH** if the installer offers it.
- Install **Ollama** for your operating system from [ollama.com/download](https://ollama.com/download), then open the Ollama app.
- VS Code is optional. You can use its terminal or Windows PowerShell / macOS Terminal.

Close and reopen your terminal after installation.

## 2. Download the project

Open [the project repository](https://github.com/subhanjanshah/Suomen_eOppimekeskus), select **Code → Download ZIP**, and extract it. If it is private, sign in with a GitHub account that has repository access.

Open the extracted folder in VS Code, then select **Terminal → New Terminal**. Make sure the terminal is in the folder containing `streamlit_app.py`, `local_auth.py`, and `.streamlit/config.toml`.

Alternatively, open your normal terminal and navigate there:

```text
cd "PASTE THE FULL PATH TO THE EXTRACTED PROJECT FOLDER HERE"
```

Replace the example path with your actual folder path, keeping the quotes.

## 3. Download the AI model

Run these commands on either operating system:

```bash
ollama --version
ollama pull qwen2.5:7b
ollama list
```

The first download may take several minutes. Confirm `qwen2.5:7b` appears in the list; this is the model the current code uses.

If Ollama reports that it cannot connect, open the Ollama application. Alternatively, run `ollama serve` in a separate terminal and leave it running. If it says the address is already in use, Ollama may already be running—do not start a second copy.

## 4. Set up Python and create your login

Run **only the block for your operating system**, from the project folder. Virtual-environment activation is not needed with these commands.

**Windows — PowerShell:**

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install streamlit==1.63.0 requests newspaper3k lxml_html_clean ddgs feedparser Pillow
.\.venv\Scripts\python.exe local_auth.py add-user editor
```

**macOS — Terminal:**

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install streamlit==1.63.0 requests newspaper3k lxml_html_clean ddgs feedparser Pillow
.venv/bin/python local_auth.py add-user editor
```

Check that the Python version shown is at least 3.12. Replace `editor` with your preferred username if you want. Enter a password of **at least 12 characters**, then confirm it. Nothing appears while you type the password; this is normal. Create the account only once. Do not share or upload `.local/accounts.json`.

## 5. Start the website

**Windows:**

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

**macOS:**

```bash
.venv/bin/python -m streamlit run streamlit_app.py --server.address 127.0.0.1
```

Open [http://localhost:8501](http://localhost:8501) and sign in with the account you created. Keep the terminal open while using the app.

For a first test, paste one article link, generate a draft, select the article, prepare and review its Finnish translation, then build the newsletter. AI processing can take time; start with a small number of articles.

## Next time and shutting down

- **Next time:** open Ollama, open a terminal in the project folder, and run the Step 5 command. No reinstall or new account is needed.
- **Stop the website:** press **Ctrl+C** in its terminal (also on Mac).
- **Unload Qwen:** run `ollama stop qwen2.5:7b`. Quit Ollama too if you are finished using it.

If a command is not found, reopen the terminal and check the corresponding installation. If `streamlit_app.py` cannot be found, the terminal is in the wrong folder. If an article produces no result, try a direct public article URL; some websites block extraction.

These instructions match the current local Streamlit prototype. Streamlit 1.63.0 matches the development environment; a fresh Windows installation has not been tested here. Do not expose this local prototype directly to the public internet.
