 AI Test Case Generator — Jira + Claude (Anthropic)  
HOW TO RUN:
  1. pip install anthropic requests python-dotenv
  2. Copy .env.example → .env and fill in your keys
  3. python generate_test_cases.py
     
What this script does:
  • Reads a Jira story (or a whole sprint's stories)
  • Sends each story to Claude AI with a QA prompt
  • Gets back structured test cases
  • Posts them as a comment on the Jira story
