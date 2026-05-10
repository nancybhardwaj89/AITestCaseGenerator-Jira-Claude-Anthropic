"""
╔══════════════════════════════════════════════════════════╗
║   AI Test Case Generator — Jira + Claude (Anthropic)    ║
║   Beginner-friendly, heavily commented                   ║
╚══════════════════════════════════════════════════════════╝

HOW TO RUN:
  1. pip install anthropic requests python-dotenv
  2. Copy .env.example → .env and fill in your keys
  3. python generate_test_cases.py

What this script does:
  • Reads a Jira story (or a whole sprint's stories)
  • Sends each story to Claude AI with a QA prompt
  • Gets back structured test cases
  • Posts them as a comment on the Jira story
"""

import os
import json
import requests
from base64 import b64encode
from dotenv import load_dotenv
import anthropic

# ── Load your secret keys from the .env file ──────────────
load_dotenv()

JIRA_EMAIL    = os.getenv("JIRA_EMAIL")
JIRA_TOKEN    = os.getenv("JIRA_TOKEN")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL")  # e.g. https://yourcompany.atlassian.net
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")

# ── Jira needs Basic Auth (email + token, base64-encoded) ──
credentials   = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
encoded_creds = b64encode(credentials.encode()).decode()
JIRA_HEADERS  = {
    "Authorization": f"Basic {encoded_creds}",
    "Content-Type":  "application/json",
    "Accept":        "application/json",
}

# ── Anthropic client ────────────────────────────────────────
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ════════════════════════════════════════════════════════════
#  STEP 1 — FETCH A SINGLE JIRA STORY
# ════════════════════════════════════════════════════════════
def get_jira_story(issue_key: str) -> dict:
    """
    Fetches one Jira issue by its key, e.g. 'PROJ-123'.
    Returns a clean dict with the fields we care about.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    response = requests.get(url, headers=JIRA_HEADERS)

    # Stop if Jira returned an error
    response.raise_for_status()

    data   = response.json()
    fields = data["fields"]

    # ── Extract the story title ────────────────────────────
    title = fields.get("summary", "No title")

    # ── Extract the description ────────────────────────────
    # Jira uses Atlassian Document Format (ADF) — we pull
    # only the plain text parts to keep things simple
    description = extract_text_from_adf(fields.get("description"))

    # ── Extract acceptance criteria ────────────────────────
    # "Acceptance Criteria" is often a custom field.
    # Common field names: customfield_10016, customfield_10034
    # Check yours at: JIRA_BASE_URL/rest/api/3/field
    acceptance_criteria = extract_text_from_adf(
        fields.get("customfield_10016")   # ← change this to your field ID
    )

    story = {
        "key":                 issue_key,
        "title":               title,
        "description":         description,
        "acceptance_criteria": acceptance_criteria,
    }

    print(f"✅ Fetched story: [{issue_key}] {title}")
    return story


def extract_text_from_adf(adf_content) -> str:
    """
    Jira stores rich text in Atlassian Document Format (ADF),
    which is a nested JSON structure. This helper pulls out
    all the plain text so we can feed it to Claude.
    """
    if not adf_content:
        return "Not provided"

    # If it's already a plain string, return as-is
    if isinstance(adf_content, str):
        return adf_content

    texts = []

    def recurse(node):
        if isinstance(node, dict):
            # A "text" node holds actual content
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            # Recurse into child nodes
            for child in node.get("content", []):
                recurse(child)
        elif isinstance(node, list):
            for item in node:
                recurse(item)

    recurse(adf_content)
    return " ".join(texts).strip() or "Not provided"


# ════════════════════════════════════════════════════════════
#  STEP 2 — FETCH ALL STORIES FROM AN OPEN SPRINT
#           (optional — use this instead of get_jira_story
#            if you want to process a whole sprint at once)
# ════════════════════════════════════════════════════════════
def get_stories_from_sprint(project_key: str) -> list[dict]:
    """
    Returns all user stories in the current open sprint
    for the given project, e.g. project_key='PROJ'.
    """
    # JQL = Jira Query Language — like SQL for Jira issues
    jql   = (
        f"project = {project_key} "
        f"AND issuetype = Story "
        f"AND sprint in openSprints() "
        f"ORDER BY created DESC"
    )
    url    = f"{JIRA_BASE_URL}/rest/api/3/search"
    params = {
        "jql":        jql,
        "maxResults": 50,       # increase if you have more
        "fields":     "summary,description,customfield_10016",
    }

    response = requests.get(url, headers=JIRA_HEADERS, params=params)
    response.raise_for_status()

    issues  = response.json().get("issues", [])
    stories = []

    for issue in issues:
        fields = issue["fields"]
        stories.append({
            "key":                 issue["key"],
            "title":               fields.get("summary", "No title"),
            "description":         extract_text_from_adf(fields.get("description")),
        })

    print(f"✅ Found {len(stories)} stories in open sprint for project '{project_key}'")
    return stories


# ════════════════════════════════════════════════════════════
#  STEP 3 — ASK CLAUDE TO GENERATE TEST CASES
# ════════════════════════════════════════════════════════════
def generate_test_cases(story: dict) -> list[dict]:
    """
    Sends the Jira story to Claude and asks for structured
    test cases. Returns a list of test case dicts.
    """

    # ── Build the prompt ───────────────────────────────────
    prompt = f"""You are an experienced QA engineer.
Given the following Jira user story, write comprehensive test cases.

USER STORY
==========
Title: {story['title']}

Description:
{story['description']}

Acceptance Criteria:
{story['acceptance_criteria']}

INSTRUCTIONS
============
Write test cases that cover:
1. Happy path (normal, expected usage)
2. Edge cases (boundary values, unusual but valid inputs)
3. Negative scenarios (invalid inputs, error handling)

Respond ONLY with a valid JSON array. No explanation text before or after.
Each item in the array must have exactly these keys:
  - "title":          short name of the test case
  - "type":           one of "happy_path", "edge_case", "negative"
  - "preconditions":  what must be true before running the test
  - "steps":          array of strings, each a numbered action
  - "expected_result": what should happen if the test passes

Example of the expected format:
[
  {{
    "title": "Successful login with valid credentials",
    "type": "happy_path",
    "preconditions": "User has an active account",
    "steps": [
      "1. Navigate to the login page",
      "2. Enter a valid email address",
      "3. Enter the correct password",
      "4. Click the Login button"
    ],
    "expected_result": "User is redirected to the dashboard and sees a welcome message"
  }}
]"""

    print(f"🤖 Sending story [{story['key']}] to Claude...")

    # ── Call the Claude API ────────────────────────────────
    message = claude.messages.create(
        model      = "claude-sonnet-4-5",   # Use Sonnet for speed + quality
        max_tokens = 4096,                          # Enough for ~10-15 test cases
        messages   = [
            {"role": "user", "content": prompt}
        ]
    )

    raw_response = message.content[0].text

    # ── Parse the JSON response ────────────────────────────
    try:
        # Claude sometimes wraps JSON in markdown fences — strip them
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        test_cases = json.loads(clean.strip())
        print(f"✅ Claude generated {len(test_cases)} test cases")
        return test_cases

    except json.JSONDecodeError:
        print("⚠️  Claude's response wasn't valid JSON. Saving raw text instead.")
        # Fall back: return as a single raw entry
        return [{"title": "Raw output", "raw": raw_response}]


# ════════════════════════════════════════════════════════════
#  STEP 4 — FORMAT TEST CASES AS READABLE TEXT
# ════════════════════════════════════════════════════════════
def format_test_cases_for_jira(test_cases: list[dict]) -> str:
    """
    Converts the list of test case dicts into a nicely
    formatted string to post as a Jira comment.
    """
    TYPE_EMOJI = {
        "happy_path": "✅",
        "edge_case":  "⚠️",
        "negative":   "❌",
    }

    lines = ["*AI-Generated Test Cases* (via Claude)\n", "----"]

    for i, tc in enumerate(test_cases, start=1):
        # Handle fallback raw output
        if "raw" in tc:
            lines.append(tc["raw"])
            continue

        emoji = TYPE_EMOJI.get(tc.get("type", ""), "🔹")
        lines.append(f"\n*TC-{i:02d}: {tc.get('title', 'Untitled')}* {emoji}")
        lines.append(f"*Type:* {tc.get('type', 'N/A').replace('_', ' ').title()}")
        lines.append(f"*Preconditions:* {tc.get('preconditions', 'None')}")
        lines.append("*Steps:*")
        for step in tc.get("steps", []):
            lines.append(f"  {step}")
        lines.append(f"*Expected Result:* {tc.get('expected_result', 'N/A')}")
        lines.append("----")

    return "\n".join(lines)


# ════════════════════════════════════════════════════════════
#  STEP 5 — POST TEST CASES BACK TO JIRA AS A COMMENT
# ════════════════════════════════════════════════════════════
def post_comment_to_jira(issue_key: str, comment_text: str):
    """
    Adds a comment to the Jira issue with the generated
    test cases so your team can see them right in Jira.
    """
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    # Jira comments use Atlassian Document Format (ADF)
    # This creates a simple paragraph comment
    payload = {
        "body": {
            "type":    "doc",
            "version": 1,
            "content": [
                {
                    "type":    "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment_text
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=JIRA_HEADERS, json=payload)
    response.raise_for_status()
    print(f"✅ Test cases posted as comment on [{issue_key}]")


# ════════════════════════════════════════════════════════════
#  STEP 6 — ALSO SAVE RESULTS LOCALLY AS JSON (BONUS)
# ════════════════════════════════════════════════════════════
def save_to_file(issue_key: str, test_cases: list[dict]):
    """
    Saves the generated test cases to a local JSON file.
    Useful for your records or to import into a test tool.
    """
    filename = f"test_cases_{issue_key}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(test_cases, f, indent=2, ensure_ascii=False)
    print(f"💾 Test cases saved locally → {filename}")


# ════════════════════════════════════════════════════════════
#  MAIN — Wire everything together
# ════════════════════════════════════════════════════════════
def process_single_story(issue_key: str):
    """
    Full pipeline for ONE story.
    Replace 'PROJ-123' with your actual issue key.
    """
    print(f"\n{'═'*55}")
    print(f"  Processing story: {issue_key}")
    print(f"{'═'*55}")

    # 1. Fetch the story from Jira
    story = get_jira_story(issue_key)

    # 2. Generate test cases with Claude
    test_cases = generate_test_cases(story)

    # 3. Format for Jira comment
    comment = format_test_cases_for_jira(test_cases)

    # 4. Post back to Jira
    post_comment_to_jira(issue_key, comment)

    # 5. Save locally as backup
    save_to_file(issue_key, test_cases)

    print(f"\n🎉 Done! Check your Jira story [{issue_key}] for the test cases.\n")


def process_full_sprint(project_key: str):
    """
    Full pipeline for ALL stories in the current open sprint.
    Replace 'PROJ' with your Jira project key.
    """
    stories = get_stories_from_sprint(project_key)

    for story in stories:
        try:
            test_cases = generate_test_cases(story)
            comment    = format_test_cases_for_jira(test_cases)
            post_comment_to_jira(story["key"], comment)
            save_to_file(story["key"], test_cases)
        except Exception as e:
            # Don't stop for one failed story — log and continue
            print(f"❌ Error on {story['key']}: {e}")

    print(f"\n🎉 Sprint processing complete! {len(stories)} stories processed.\n")


# ── Entry point ────────────────────────────────────────────
if __name__ == "__main__":

    # ┌─────────────────────────────────────────────┐
    # │  CHOOSE ONE of the two options below:        │
    # └─────────────────────────────────────────────┘

    # OPTION A: Process a single story
    process_single_story("SCRUM-1")        # ← change to your issue key

    # OPTION B: Process all stories in the current sprint
    # process_full_sprint("PROJ")           # ← change to your project key