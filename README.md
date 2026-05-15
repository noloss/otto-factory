# otto-factory

**Turn a requirements document into working, tested, reviewed code without writing a single line yourself.**

otto-factory is an AI pipeline that acts as your development team. You describe what you want to build, and three AI agents handle the rest: one breaks the work into tasks, one writes the code, and one reviews it. Every task lives as a GitHub Issue so you can follow along and understand exactly what is happening at every step.

## Why otto-factory?

Most AI coding tools require an **Anthropic API key**, which is a separate paid account billed by the token. Every word the AI reads or writes costs money on top of your subscription. This can get expensive fast when running automated pipelines.

**otto-factory is different.** It runs on top of the `claude` command-line tool, which is included with your **Claude Pro or Claude Max subscription** — no API key, no per-token charges beyond your monthly subscription fee.


On top of that, otto-factory uses **GitHub Issues as its memory**. Every task the AI works on is a real GitHub Issue with acceptance criteria. Every PR is a real GitHub Pull Request with a diff you can read. There are no hidden logs or black-box state — you can open GitHub at any point and see exactly what the agents are doing and why.

## How it works

You start by writing a PRD — a plain text description of what you want to build. This is the only step that involves you. 

You give the PRD to the **Planner**, who reads it and creates a set of GitHub Issues, one per feature, each with a user story and acceptance criteria. These are your projects tasks. You can freely edit the GitHub issues in GitHub, and add more details and make sure the plan is what you would expect. 

From there, the **Orchestrator** takes over and works through the issues one by one:

```
Your PRD
   │
   ▼
Planner ──────► GitHub Issues  (one per feature, labelled agent-todo)
                      │
                      ▼
               Orchestrator loop
               ┌──────┬─────────────┐
               ▼      ▼             ▼
            Coder   Tests       Reviewer
          (writes  (runs your   (reads the diff,
           code,    test suite)  approves or rejects)
           opens PR)
```

For each issue, the **Coder** creates a branch, writes the code using a test-first approach, and opens a Pull Request. The test suite then runs automatically. If the tests pass, the **Reviewer** reads the changes (the diff) and checks it against the acceptance criteria of the user story. If everything looks good, the PR is merged and the issue is closed. If the Reviewer finds problems, the feedback is sent back to the Coder for another attempt — up to three times before it flags the issue for your attention.

Because GitHub is the backbone, you always know what is happening. Watch GitHub Issues move from `agent-todo` to `agent-in-progress` to `review-needed` in real time, read the code diff before it merges, and see the reviewer's comments directly on the PR — just like a real development team would work.

---

## What you will need

Before starting, make sure you have these three things installed on your computer:

| Tool | What it is | How to get it |
|---|---|---|
| **Claude Code** (`claude`) | The AI engine — included with Claude Pro/Max | [claude.ai/code](https://claude.ai/code) |
| **GitHub CLI** (`gh`) | Lets the app talk to GitHub from your terminal | [cli.github.com](https://cli.github.com) |
| **Python 3.10+** | The language the app is written in | [python.org](https://www.python.org/downloads/) |

You will also need:
- A **GitHub account**
- A **Claude Pro or Claude Max subscription**


> ⚠️ If you have an `ANTHROPIC_API_KEY` variable set in your terminal environment, the `claude` tool will use that instead of your subscription and you will be billed per-token. Remove it or unset it before running otto-factory if you want to use your Claude Pro or Max subscription. (If you don't know what that means, you probably don't have the key and don't need to worry about it.)

---

## How projects and otto-factory relate

otto-factory is installed once and reused for every project. Each project you want to build lives in its own folder and has its own small config file (`.otto`):

```
~/
├── otto-factory/               ← the factory (installed once)
│   ├── .env                    ← machine-level config (tool paths, global defaults)
│   └── ...
├── my-first-project/           ← project A
│   ├── .otto                   ← project config (GITHUB_REPO, TEST_COMMAND, …)
│   ├── CLAUDE.md               ← optional: project-specific coder instructions
│   └── src/
└── my-second-project/          ← project B
    ├── .otto
    └── src/
```

To run otto-factory on a project, either **`cd` into the project directory** or use the `--project` flag:

```bash
# Option A — cd into the project first (the natural workflow from VS Code)
cd ~/my-first-project
python ~/otto-factory/main.py run --milestone "Release 1"

# Option B — explicit flag, run from anywhere
python ~/otto-factory/main.py --project ~/my-first-project run --milestone "Release 1"
```

Think of `otto-factory` as a contractor's toolbox. Each project is a different building site — you bring the same toolbox to each one.

> **Tip:** Each code block below has a copy button in its top-right corner when viewed on GitHub. Click it to copy the command, then paste it into your terminal.

---

## Installation (do this once)

Open your **terminal** (on Mac: search for "Terminal" in Spotlight; on Windows: use "Command Prompt" or "PowerShell") and run these commands one at a time.

**1. Go to the folder where you want otto-factory to live** (your home directory is a good choice):

```
cd ~
```

**2. Download otto-factory** — this creates an `otto-factory/` folder here:

```
git clone https://github.com/your-org/otto-factory.git
```

**3. Enter the folder:**

```
cd otto-factory
```

**4. Set up a Python environment:**

```
python3 -m venv venv
```

**5. Activate the environment** — run this every time you open a new terminal window before using otto-factory:

On Mac/Linux:
```
source venv/bin/activate
```

On Windows:
```
venv\Scripts\activate
```

**6. Install dependencies:**

```
pip install -r requirements.txt
```

---

## Running the pipeline on your own projects

Activate the otto-factory environment at the start of each session:

On Mac/Linux:
```bash
source ~/otto-factory/venv/bin/activate
```

On Windows:
```
~/otto-factory/venv/Scripts/activate
```

> **What is `venv` and why activate it?** A virtual environment (`venv`) is an isolated space that holds the Python packages otto-factory depends on, separate from everything else on your computer. Activating it tells Python to use that space for this session. Without it, Python won't find the `factory` package and commands will fail. You need to activate it once per terminal window — it does not persist between sessions.

All examples below assume you have `cd`'d into your project directory. Replace `~/otto-factory/main.py` with the actual path to your otto-factory installation.

### Create tasks from a PRD

```bash
cd ~/my-project
python ~/otto-factory/main.py plan --prd path/to/your/prd.md
```

This reads your PRD, creates a GitHub Milestone, and breaks it into GitHub Issues — each with a user story and acceptance criteria. Open your GitHub repo and you will see them appear under **Issues**.

### Run the full pipeline for a milestone

```bash
cd ~/my-project
python ~/otto-factory/main.py run --milestone "Release 1"
```

This kicks off the automated loop. For each issue, the agents will:

1. **Coder** — create a branch, write code, open a Pull Request
2. **Tests** — run your test suite automatically (if `TEST_COMMAND` is configured in `.otto`)
3. **Reviewer** — read the PR diff, approve and merge it, or send feedback back to the coder

You can follow the progress on GitHub in real time. Issues move through labels as work progresses:

```
agent-todo  →  agent-in-progress  →  review-needed  →  merged (closed)
                                                ↑
                                    revision-needed (if reviewer rejects)
```

### Run individual agents manually

Re-run the coder on a specific issue (replace `42` with your issue number):

```bash
python ~/otto-factory/main.py code --issue 42
```

Re-run the reviewer on a specific PR (replace `99` with your PR number):

```bash
python ~/otto-factory/main.py review --pr 99
```

---

## Try it yourself — build your first project

The best way to learn otto-factory is to run it on a real example. This repository includes a ready-made PRD (`prd-example.md`) that asks the agents to build a simple webpage promoting otto-factory. It is a great first test — it is small, has no backend, and produces something you can open directly in your browser when it is done.

Follow the steps below using `my-first-project` as your project name. Once you have done it once, you will know exactly how to repeat it for your own ideas.

### Step 1 — Create the project repo on GitHub

Go to [github.com/new](https://github.com/new) and create a new empty repository named **`my-first-project`**. Leave it empty for now.

### Step 2 — Clone it to your computer

Open a terminal. Go to your home directory (not inside `otto-factory`):

```
cd ~
```

Clone your new project (replace `YOUR-USERNAME` with your GitHub username):

```
git clone https://github.com/YOUR-USERNAME/my-first-project.git
```

Enter the project folder:

```
cd my-first-project
```

Create an empty first commit so the coder has a branch to start from:

```
git commit --allow-empty -m "init"
```

Push it to GitHub:

```
git push -u origin main
```

### Step 3 — Configure this project

From inside `my-first-project`, create a `.otto` config file from the template:

```bash
cp ~/otto-factory/.otto.example ~/my-first-project/.otto
```

Open `~/my-first-project/.otto` in a text editor and fill in these values (replace `YOUR-USERNAME` with your GitHub username):

```ini
GITHUB_REPO=YOUR-USERNAME/my-first-project
TEST_COMMAND=
SOURCE_GLOB=.
```

Save the file. That's it — otto-factory picks up `.otto` automatically when you run commands from this directory.

### Step 4 — Run the planner

Make sure the otto-factory environment is active, then run from inside `my-first-project`:

```bash
cd ~/my-first-project
python ~/otto-factory/main.py plan --prd ~/otto-factory/prd-example.md
```

Open your `my-first-project` repo on GitHub. You should see a new Milestone called **Release 1** and several Issues under the Issues tab — one per feature of the webpage. Each issue has a user story and acceptance criteria written by the planner.

### Step 5 — Run the full pipeline

```bash
cd ~/my-first-project
python ~/otto-factory/main.py run --milestone "Release 1"
```

Watch your terminal as the agents work. When they finish, open your `my-first-project` repo on GitHub — you will see merged Pull Requests and a closed milestone. Pull the repo and open `index.html` in your browser to see the result.

### Try it now — run the reviewer manually

Once the pipeline has run and PR #1 exists, you can trigger the reviewer on it directly:

```bash
python ~/otto-factory/main.py review --pr 1
```

---

## Configuration reference

Settings are split across two files:

**`otto-factory/.env`** — machine-level defaults, set once for all projects:

| Setting | Default | What it does |
|---|---|---|
| `GH_BIN` | `gh` | Path to the gh CLI (only change if `which gh` returns a custom path) |
| `CLAUDE_BIN` | `claude` | Path to the claude CLI (only change if `which claude` returns a custom path) |
| `CODER_TIMEOUT` | `600` | Seconds before the coder gives up on an issue (10 minutes) |
| `MAX_ATTEMPTS` | `3` | How many times to retry a failing issue before giving up |
| `SHELL_INIT` | _(none)_ | Shell init command prepended to `TEST_COMMAND` (needed for nvm, pyenv, etc.) |

**`<project>/.otto`** — per-project settings, one file per project:

| Setting | Default | What it does |
|---|---|---|
| `GITHUB_REPO` | _(required)_ | GitHub repo in `owner/repo` format (or full URL) |
| `TEST_COMMAND` | _(none)_ | Command to run your tests — leave blank to skip |
| `SOURCE_GLOB` | `src` | Folder the coder stages with `git add` — use `.` if files are at the project root |

> `TARGET_DIR` no longer needs to be set. Otto-factory uses the directory you run from (or pass with `--project`) as the project root automatically.

### Per-project CLAUDE.md

Place a `CLAUDE.md` file in your project root to give the coder agent project-specific instructions — coding conventions, architecture notes, things to avoid, or anything else that should guide how it writes code. Claude Code picks this file up automatically when running in that directory.

Example `~/my-project/CLAUDE.md`:
```markdown
# my-project coding conventions

- This project uses Tailwind CSS — do not write custom CSS
- All API routes live in src/routes/ and follow REST conventions
- Use TypeScript strict mode — no `any` types
```

---

## Project structure (for the curious)

```
otto-factory/               ← install once, reuse for every project
├── main.py                 ← The CLI you run
├── requirements.txt        ← Python dependencies
├── .env.example            ← Machine-level config template
├── .otto.example           ← Per-project config template (copy to each project)
├── prd-example.md          ← A ready-made PRD to try on your first project
├── tests/                  ← Automated test suite (pytest)
└── factory/
    ├── config.py           ← Loads .env (machine) + .otto (project)
    ├── github_client.py    ← Talks to GitHub via the gh CLI
    ├── llm_engine.py       ← Talks to Claude via the claude CLI
    ├── planner.py          ← Planner agent
    ├── coder.py            ← Coder agent
    ├── reviewer.py         ← Reviewer agent
    ├── orchestrator.py     ← Runs the loop and coordinates agents
    └── prompts/            ← Instructions given to each agent

my-project/                 ← one per project you build
├── .otto                   ← Project config (GITHUB_REPO, TEST_COMMAND, …)
├── CLAUDE.md               ← Optional: coder instructions for this project
└── src/
```
