# 🚀 AI Test Case Generator — Jira + Claude (Anthropic)

Automatically generate structured QA test cases from Jira stories using Claude AI and post them back to Jira as comments.

---

## ✨ Features

* 📖 Reads a single Jira story or an entire sprint
* 🤖 Sends story details to Claude AI (Anthropic)
* 🧪 Generates structured QA test cases automatically
* 💬 Posts generated test cases directly as Jira comments
* ⚡ Saves manual QA effort and speeds up test preparation

---

# 🛠️ Tech Stack

| Technology            | Purpose                             |
| --------------------- | ----------------------------------- |
| Python                | Core scripting                      |
| Jira API              | Fetching stories & posting comments |
| Claude AI (Anthropic) | AI-powered test case generation     |
| python-dotenv         | Environment variable management     |
| Requests              | API communication                   |

---

# 📂 Project Flow

```mermaid
flowchart LR
    A[Jira Story / Sprint] --> B[Python Script]
    B --> C[Claude AI Prompt]
    C --> D[Generated Test Cases]
    D --> E[Post Comment to Jira]
```

---

# ⚙️ Installation

## 1️⃣ Install Dependencies

```bash
pip install anthropic requests python-dotenv
```

---

## 2️⃣ Configure Environment Variables

Copy:

```bash
.env.example
```

To:

```bash
.env
```

Then add your credentials:

```env
ANTHROPIC_API_KEY=your_claude_api_key
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_email
JIRA_API_TOKEN=your_jira_api_token
```

---

## 3️⃣ Run the Script

```bash
python generate_test_cases.py
```

---

# 🔥 What This Script Does

### Step 1 — Read Jira Stories

* Fetches a Jira story
* OR fetches all stories from a sprint

### Step 2 — Send to Claude AI

* Creates a QA-focused AI prompt
* Sends story details to Claude AI

### Step 3 — Generate Test Cases

* Claude returns structured test cases
* Includes positive, negative, and edge scenarios

### Step 4 — Update Jira

* Posts generated test cases as comments
* Keeps everything linked to the original Jira story

---

# 🧪 Example Output

```text
Test Case ID: TC_LOGIN_001
Scenario: Valid User Login
Steps:
1. Open application
2. Enter valid username and password
3. Click Login

Expected Result:
User should successfully login and navigate to dashboard.
```

---

# 📌 Use Cases

* Agile QA teams
* Sprint test preparation
* Automation-ready test design
* Faster regression planning
* AI-assisted QA documentation

---

# 📈 Future Enhancements

* ✅ Export test cases to Excel
* ✅ Generate automation-ready scripts
* ✅ Support Azure DevOps
* ✅ Slack/Teams integration
* ✅ Test case categorization

---

# 🤝 Contributing

Contributions, ideas, and improvements are welcome.

Feel free to fork the project and submit a PR.

---

# ⭐ Support

If you found this project useful:

* Star the repository ⭐
* Share with QA teams 👨‍💻
* Contribute improvements 🚀

