# otto-factory

**Turn a requirements document into working, tested, reviewed code without writing a single line of code yourself.**

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

## The two-folder setup

otto-factory works with **two separate folders** on your computer:

```
~/                              ← your home directory
├── otto-factory/               ← the factory itself (this repo)
└── my-first-project/           ← the project you want to build
```

- **`otto-factory/`** is the tool. You install it once and reuse it for every project. You always run commands from here.
- **`my-first-project/`** is where the generated code will live. The agents write files here and open Pull Requests on its GitHub repository.

Think of `otto-factory` as a contractor's toolbox, and `my-first-project` as the building site.

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

All commands below are run from **inside the `otto-factory` folder**. Open a terminal and run these at the start of every session:

```
cd ~/otto-factory
```

On Mac/Linux:
```
source venv/bin/activate
```

On Windows:
```
venv\Scripts\activate
```

> **What is `venv` and why activate it?** A virtual environment (`venv`) is an isolated space that holds the Python packages otto-factory depends on, separate from everything else on your computer. Activating it tells Python to use that space for this session. Without it, Python won't find the `factory` package and commands will fail. You need to activate it once per terminal window — it does not persist between sessions.

### Create tasks from a PRD

```
python main.py plan --prd path/to/your/prd.md
```

This reads your PRD, creates a GitHub Milestone, and breaks it into GitHub Issues — each with a user story and acceptance criteria. Open your GitHub repo and you will see them appear under **Issues**.

### Run the full pipeline for a milestone

```
python main.py run --milestone "Release 1"
```

This kicks off the automated loop. For each issue, the agents will:

1. **Coder** — create a branch, write tests, write code until the tests pass, open a Pull Request
2. **Tests** — run your test suite automatically (if `TEST_COMMAND` is configured)
3. **Reviewer** — read the PR diff, approve and merge it, or send feedback back to the coder

You can follow the progress on GitHub in real time. Issues move through labels as work progresses:

```
agent-todo  →  agent-in-progress  →  review-needed  →  merged (closed)
                                                ↑
                                    revision-needed (if reviewer rejects)
```

If the coder gets stuck on an issue that is too large, it is automatically split into smaller sub-issues and each one is retried.

### Run individual agents manually

Re-run the coder on a specific issue (replace `42` with your issue number):

```
python main.py code --issue 42
```

Re-run the reviewer on a specific PR (replace `99` with your PR number):

```
python main.py review --pr 99
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

### Step 3 — Configure otto-factory for this project

Go back into the `otto-factory` folder:

```
cd ~/otto-factory
```

Create your configuration file from the template:

```
cp .env.example .env
```

Open the `.env` file in a text editor and fill in these values (replace `YOUR-USERNAME` and the path with your own):

```ini
GITHUB_REPO=YOUR-USERNAME/my-first-project

TARGET_DIR=/Users/yourname/my-first-project

TEST_COMMAND=

SOURCE_GLOB=.
```

Save the file.

### Step 4 — Run the planner

Make sure you are in the `otto-factory` folder with the environment active, then run:

```
python main.py plan --prd prd-example.md
```

Open your `my-first-project` repo on GitHub. You should see a new Milestone called **Release 1** and several Issues under the Issues tab — one per feature of the webpage. Each issue has a user story and acceptance criteria written by the planner.

### Step 5 — Run the full pipeline

```
python main.py run --milestone "Release 1"
```

Watch your terminal as the agents work. When they finish, open your `my-first-project` repo on GitHub — you will see merged Pull Requests and a closed milestone. Pull the repo and open `index.html` in your browser to see the result.

### Try it now — run the reviewer manually

Once the pipeline has run and PR #1 exists, you can trigger the reviewer on it directly:

```
python main.py review --pr 1
```

---

## Configuration reference

| Setting | Default | What it does |
|---|---|---|
| `GITHUB_REPO` | _(required)_ | Your project's GitHub repo in `owner/repo` format |
| `TARGET_DIR` | `.` | Full path to your project folder on your computer |
| `TEST_COMMAND` | _(none)_ | Command to run your tests, e.g. `pytest`, `npm test`, `go test ./...` — leave blank to skip |
| `SOURCE_GLOB` | `src` | Which folder the coder stages before committing — use `.` if your project has no `src/` subfolder |
| `CLAUDE_BIN` | `claude` | Path to the claude CLI (only change if `which claude` returns a custom path) |
| `GH_BIN` | `gh` | Path to the gh CLI (only change if `which gh` returns a custom path) |
| `CODER_TIMEOUT` | `600` | Seconds before the coder is killed and the issue is split (10 minutes) |
| `MAX_ATTEMPTS` | `3` | How many times to retry a failing issue before giving up |

---

## Project structure (for the curious)

```
otto-factory/
├── main.py                 ← The CLI you run
├── requirements.txt        ← Python dependencies
├── .env.example            ← Config template
├── prd-example.md          ← A ready-made PRD to try on your first project
└── factory/
    ├── config.py           ← Reads your .env settings
    ├── github_client.py    ← Talks to GitHub via the gh CLI
    ├── llm_engine.py       ← Talks to Claude via the claude CLI
    ├── planner.py          ← Planner agent
    ├── coder.py            ← Coder agent
    ├── reviewer.py         ← Reviewer agent
    ├── orchestrator.py     ← Runs the loop and coordinates agents
    └── prompts/            ← Instructions given to each agent
```
