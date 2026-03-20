---
name: daily-diary
description: >
  Auto-generate daily diary from AI agent activity logs and Obsidian vault changes.
  At the end of a day, turn AI agent activity history and Obsidian vault changes
  into a reusable diary entry. Use this when the user asks for a daily diary,
  today's diary, yesterday's diary, or a diary for a specific date.
---

# Daily Diary

Generate a diary entry in Daily Notes by combining AI agent activity logs with
Obsidian vault changes.

## Setup

```
VAULT_PATH=/Users/choegihwan/Documents/Projects/Obsidian-frontend-journey
DAILY_NOTES_DIR={VAULT_PATH}/Daily Notes
HISTORY_FILE=${AGENT_HISTORY_FILE:-~/.claude/history.jsonl}
SCRIPT_PATH=${SKILL_DIR}/scripts/extract_history.py
```

## Workflow

### Step 1: Decide the date

- Default to today's date in `YYYY-MM-DD` format.
- If the user specifies a date such as yesterday or `2026-02-10`, use that date instead.
- Store the result in the `DATE` variable as `YYYY-MM-DD`.

### Step 2: Extract agent activity

Run the Python script to extract agent activity for the selected date.

```bash
python3 ${SKILL_DIR}/scripts/extract_history.py --date {DATE}
```

The script does the following:
- filters user requests from `${AGENT_HISTORY_FILE}` for the target date
- groups them by project and sorts them chronologically
- collects `git log` entries for the same date from each project directory
- prints structured text to stdout

If the script output is empty or says `No activity`, treat it as "there was no
agent activity on that day."

### Step 3: Extract Obsidian vault changes

Run the following directly in bash.

```bash
cd "/Users/choegihwan/Documents/Projects/Obsidian-frontend-journey"

# Commit list for the target date
COMMITS=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h %s" 2>/dev/null)

if [ -n "$COMMITS" ]; then
  echo "$COMMITS"

  # Extract the first and last commit hashes
  FIRST=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h" --reverse 2>/dev/null | head -1)
  LAST=$(git log --since="{DATE} 00:00:00" --until="{DATE} 23:59:59" --format="%h" 2>/dev/null | head -1)

  # Stats for changed markdown files, excluding .obsidian
  git diff --stat "${FIRST}^..${LAST}" -- '*.md' ':!.obsidian' 2>/dev/null
fi
```

If there are no commits, omit the notes activity section.

### Step 4: Write the diary

You are an editor turning a day's activity log into a diary entry people would
want to reread, and into a record that can later be reused as resume material.

The goal is not to list logs mechanically, but to organize the day naturally as:
`why it was done -> what was done -> what remains`.

#### Never do this
- Do not include the writing process, decision criteria, or constraints in the diary body.
- Do not output meta phrases such as:
  - "I used only the provided facts"
  - "the request scope was limited"
  - `total requests`
  - `decision signals`
  - "I filled the structure"
  - "I stated the evidence"
  - "I decided to write"
  - raw count phrases such as `N commits` or `N changed md files`
- Do not turn backup / wip / temp style commit messages directly into activity narration.
- Do not replace prose with a list of file paths.
- Do not invent uncertain facts. You may still generalize upward from file names,
  folder names, and user requests when the generalization is clearly safe.

#### Interpretation rules
1. Use user requests as evidence of intent.
2. Use created or modified files and notes as evidence of output.
3. Use git history only as proof that the work actually happened.
4. Group files pointing to the same topic into one piece of work.
5. Even when the activity is small, do not exaggerate. Prefer conservative verbs
   such as organized, reinforced, connected, documented, refined, visualized, and maintained.

#### Priority order
Write the most important items first in this order:
1. newly created outputs and clearly completed work
2. structural improvements, automation, and problem solving
3. study notes, documentation, and visualization
4. plain backups and format-only changes

#### Output rules
- Write the diary body in Korean.
- Write only 2-4 core bullets per project.
- Each bullet should be a single sentence following:
  `what was done + why/how it was done + what result remains`.
- Do not include unnecessary times, request counts, or commit counts.
- Do not add sections beyond the template.
- Write `### 🧾 Career Assets` only when the evidence is strong enough for 1-3 bullets;
  omit it when the evidence is weak.
- Write the reflection in 1-2 sentences.

#### Output template

```markdown
---

## 📝 Daily Diary

### 🖥️ Development Work

#### {Project Name}
- ...
- ...

### 📓 Notes Activity
- Newly written notes: [[...]]
- Updated notes: [[...]]

### 🧾 Career Assets
- ...
- ...

### 💭 Reflection
...
```

### Step 5: Save the file

Target file: `{DAILY_NOTES_DIR}/{DATE}.md`

**Three cases:**

1. **If the file does not exist**: create it and write the diary content.
2. **If the file exists and has no `## 📝 Daily Diary` section**: append the diary at the end with a `---` separator.
3. **If the file exists and already has a `## 📝 Daily Diary` section**: replace only that section to preserve idempotence.
   - Use the range from `## 📝 Daily Diary` to the next `---` or the end of file.

**Important:** Do not overwrite the entire file with the Write tool. Existing Daily Notes content must be preserved.
- Case 2: read the existing content first, then append the diary with Write.
- Case 3: read the file first, then replace only the diary section with Edit.
