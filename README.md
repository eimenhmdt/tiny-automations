# Tiny Automations

A growing collection of small, focused automations for foundersthat reduce noise and free up space for genuine connection and the important things in life.

## ✨ Current Automations

- **Email Triage (macOS)**  
  Automatically classifies your Apple Mail inbox using OpenAI and applies color-coded flags for quick scanning and action.

## 📬 Email Triage Setup (macOS Only)

This automation uses AppleScript to interact with Apple Mail and OpenAI (GPT-4o-mini) to classify emails.

**Prerequisites:**

- macOS
- Apple Mail
- Python 3.x
- An OpenAI account and API key.

**Setup Steps:**

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/eimenhmdt/tiny-automations.git
    cd tiny-automations
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

    - Create a file named `.env` in the root directory.
    - Add your OpenAI API key to it:
      ```
      OPENAI_API_KEY="YOUR_OPENAI_API_KEY_HERE"
      ```

5.  **(Optional but improves accuracy) Add context about you:**

    - In automation/email_triage.py, update the USER_BIO variable with a short blurb about who you are and how you work.

    Example:

    ```
    USER_BIO = "I’m a founder juggling multiple businesses. I prefer short actionable emails, and prioritize anything urgent, time-sensitive, or from existing clients."
    ```

6.  **(Optional but Recommended) Rename Mail Flags:**
    - In Apple Mail, go to `Preferences` > `Flags`.
    - Rename your flag names to match the classifications used in the script for clarity:
      - Red -> `alert`
      - Orange -> `respond`
      - Green -> `interesting`
      - Blue -> `fyi`
      - Purple -> `idk`
      - Gray -> `delete`
    - If you don't rename them, the script will still apply the correct _color_, but the flag name in Mail will remain the default (e.g., "Red").

**Usage:**

- Run the script from the root directory:
  ```bash
  python automation/email_triage.py
  ```
- The script will fetch recent emails (last 24 hours), classify them, and apply the corresponding color flags in Apple Mail.

**Customization:**

- Feel free to modify the `LABEL_COLOR_MAP` dictionary and the classification descriptions within the `user_prompt` inside `automation/email_triage.py` to better suit your personal workflow and preferences.

---

More automations coming soon!
