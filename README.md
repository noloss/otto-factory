# otto-factory

**Turn a requirements document into working, tested, reviewed code without writing a single line yourself.**

otto-factory is an AI pipeline that acts as your development team. You describe what you want to build, and three AI agents handle the rest: one breaks the work into tasks, one writes the code, and one reviews it. Every task lives as a GitHub Issue so you can follow along and understand exactly what is happening at every step.

## Why otto-factory?

Most AI coding tools require an **Anthropic API key**, which is a separate paid account billed by the token. Every word the AI reads or writes costs money on top of your subscription. This can get expensive fast when running automated pipelines.

**otto-factory is different.** It runs on top of the `claude` command-line tool, which is included with your **Claude Pro or Claude Max subscription** — no API key, no per-token charges beyond your monthly subscription fee.

On top of that, otto-factory uses **GitHub Issues as its memory**. Every task the AI works on is a real GitHub Issue with acceptance criteria. Every PR is a real GitHub Pull Request with a diff you can read. There are no hidden logs or black-box state — you can open GitHub at any point and see exactly what the agents are doing and why.

## How it works

You start by writing a PRD — a plain text description of what you want to build. This is the only step that involves you.

You give the PRD to the **Planner**, who reads it and creates a set of GitHub Issues, one per feature, each with a user story and acceptance criteria. These are your project tasks. You can freely edit the GitHub issues in GitHub, add more details, and make sure the plan is what you would expect.

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

For each issue, the **Coder** creates a branch, writes the code, and opens a Pull Request. The test suite then runs automatically. If the tests pass, the **Reviewer** reads the changes and checks them against the acceptance criteria. If everything looks good, the PR is merged and the issue is closed. If the Reviewer finds problems, the feedback is sent back to the Coder for another attempt — up to three times before it flags the issue for your attention.

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
- A **GitHub account** — and the GitHub CLI signed in to it (`gh auth login`)
- A **Claude Pro or Claude Max subscription**

> ⚠️ If you have an `ANTHROPIC_API_KEY` variable set in your terminal environment, the `claude` tool will use that key and bill you per-token instead of using your subscription. Remove it before running otto-factory if you want to use your Claude Pro or Max subscription. If you don't know what that means, you probably don't have the key and can ignore this.

---

## How projects and otto-factory relate

Otto-factory is a toolbox, not a project itself. **You install it once in one place on your computer, and then point it at different projects whenever you want to build something.**

Each project you want to build lives in its own folder and has its own small config file (`.otto`) that tells otto-factory two things: which GitHub repository to push code to, and how to run the tests. The otto-factory folder itself has its own config file (`.env`) for machine-level settings that apply to all projects — like where to find the `claude` and `gh` programs.

```
~/
├── otto-factory/               ← the factory (installed once)
│   ├── .env                    ← machine-level config: tool paths, global defaults
│   └── ...
├── my-first-project/           ← project A
│   ├── .otto                   ← project config: GitHub repo, test command
│   ├── CLAUDE.md               ← optional: coder instructions for this project
│   └── src/
└── my-second-project/          ← project B
    ├── .otto
    └── src/
```

When you run otto-factory, it automatically reads the `.otto` file from whichever project directory you are running from (or the one you point at with `--project`).

> **Tip:** Each code block below has a copy button in its top-right corner when viewed on GitHub. Click it to copy the command, then paste it into your terminal.

---

## Installation (do this once)

Open your **terminal** (on Mac: search for "Terminal" in Spotlight; on Windows: use "Command Prompt" or "PowerShell").

**1. Go to your home directory** — this is where otto-factory will live. All the path examples in this guide assume this location. If you put it somewhere else, you will need to adjust the `~/otto-factory` parts of every command accordingly.

```
cd ~
```

**2. Download otto-factory:**

```
git clone https://github.com/your-org/otto-factory.git
```

**3. Enter the folder:**

```
cd otto-factory
```

### Option A — automatic setup (Mac/Linux)

Run the install script. It creates the Python environment, installs dependencies, and copies the config template for you:

```
bash install.sh
```

That's it. Skip to [Running the pipeline on your own projects](#running-the-pipeline-on-your-own-projects).

### Option B — manual setup (all platforms, or if you prefer to see each step)

<details>
<summary>Click to expand manual setup steps</summary>

**4. Set up a Python virtual environment** — this creates an isolated space for otto-factory's dependencies so they don't interfere with anything else on your computer:

```
python3 -m venv venv
```

**5. Activate the environment** — you need to do this once every time you open a new terminal window before using otto-factory. When it is active, you will see `(venv)` at the start of your terminal prompt.

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

**7. Create the machine-level config file** by copying the template:

```
cp .env.example .env
```

</details>

The defaults in `.env` work for most people — you can leave it as-is for now. You only need to edit it if otto-factory later complains it cannot find `claude` or `gh`, or if your project uses a language runtime managed by a version manager like `nvm` or `pyenv`. See the [Configuration reference](#configuration-reference) section for details.

---

## Running the pipeline on your own projects

Before otto-factory can work on a project, that project needs a `.otto` config file in its root folder. This file is what tells otto-factory which GitHub repository to push code to. Without it, otto-factory does not know where your project lives.

### Step 1 — Activate the environment

Do this once at the start of every terminal session before running any otto-factory commands:

On Mac/Linux:
```bash
source ~/otto-factory/venv/bin/activate
```

On Windows:
```
~/otto-factory/venv/Scripts/activate
```

You will see `(venv)` appear at the start of your prompt. Without this step, Python will not find the `factory` package and commands will fail.

### Step 2 — Set up the project config file

Copy the template into your project folder (do this once per project):

```bash
cp ~/otto-factory/.otto.example ~/my-project/.otto
```

Open `~/my-project/.otto` in a text editor. The file has comments explaining every setting. The only value you must fill in is `GITHUB_REPO` — set it to your GitHub username and repo name:

```
GITHUB_REPO=your-username/my-project
```

### Step 3 — Create tasks from a PRD

Run the planner from inside your project folder. The planner reads your PRD and turns it into a structured list of GitHub Issues — one per feature — so the coder has a clear set of tasks to work through:

```bash
cd ~/my-project
python ~/otto-factory/main.py plan --prd path/to/your/prd.md
```

Open your GitHub repo and you will see a new Milestone and a set of Issues under the Issues tab. Each issue has a user story and acceptance criteria. You can edit these before running the next step if you want to add detail or change the scope.

### Step 4 — Run the full pipeline

```bash
cd ~/my-project
python ~/otto-factory/main.py run --milestone "Release 1"
```

This kicks off the automated loop. For each open issue in the milestone, the agents will:

1. **Coder** — create a branch, write code, open a Pull Request
2. **Tests** — run your test suite automatically (if `TEST_COMMAND` is set in `.otto`)
3. **Reviewer** — read the PR diff, approve and merge it, or send feedback back to the coder

You can follow the progress on GitHub in real time. Issues move through labels as work progresses:

```
agent-todo  →  agent-in-progress  →  review-needed  →  merged (closed)
                                                ↑
                                    revision-needed (if reviewer rejects)
```

### Run individual agents manually

You can also run any single agent on its own — useful when you want to retry one issue, re-review a PR after making manual edits, or experiment:

Re-run the coder on a specific issue (replace `42` with your issue number):

```bash
python ~/otto-factory/main.py code --issue 42
```

Optionally, pass feedback to guide the retry toward a specific approach:

```bash
python ~/otto-factory/main.py code --issue 42 --feedback "Use a REST API, not GraphQL"
```

Re-run the reviewer on a specific PR (replace `99` with your PR number):

```bash
python ~/otto-factory/main.py review --pr 99
```

---

## Command reference

All commands follow this pattern:

```
python main.py [--project PATH] <command> [command flags]
```

The optional `--project PATH` flag lets you point otto-factory at your project directory without `cd`-ing into it first. If you omit it, otto-factory uses whichever directory you are currently in.

| Command | What it does | Required flags | Optional flags |
|---|---|---|---|
| `plan` | Reads a PRD, creates a GitHub Milestone and one Issue per feature | `--prd <path>` | `--project <path>` |
| `run` | Runs the full plan → code → review loop for every open issue in the milestone | `--milestone <title>` | `--project <path>` |
| `code` | Runs the coder agent on a single issue and opens a PR | `--issue <number>` | `--project <path>`, `--feedback <text>` |
| `review` | Runs the reviewer agent on a single PR | `--pr <number>` | `--project <path>` |

### Flag details

- **`--project PATH`** — Path to your project directory. Otto-factory reads `.otto` from there. Default: the current directory.
- **`--prd PATH`** — Path to your requirements document (plain text or Markdown). Used by `plan`.
- **`--milestone TITLE`** — The exact title of the GitHub Milestone to work on (e.g. `"Release 1"`). Must match what appears on GitHub. Used by `run`.
- **`--issue NUMBER`** — A GitHub issue number (e.g. `42`). Used by `code`.
- **`--pr NUMBER`** — A GitHub pull request number (e.g. `99`). Used by `review`.
- **`--feedback TEXT`** — An optional note passed to the coder when retrying an issue (e.g. `"Keep changes under 50 lines"`). Used by `code`.

### Example: run from anywhere without cd

Instead of `cd`-ing into your project first, you can use `--project` to run from any directory:

```bash
# These two are equivalent:

cd ~/my-project && python ~/otto-factory/main.py run --milestone "Release 1"

python ~/otto-factory/main.py --project ~/my-project run --milestone "Release 1"
```

---

## Try it yourself — build your first project

The best way to learn otto-factory is to run it on a real example. This repository includes a ready-made PRD (`prd-example.md`) that asks the agents to build a simple webpage promoting otto-factory. It is a great first test — it is small, has no backend, and produces something you can open directly in your browser when it is done.

### Before you start — assumptions

> These steps make the following assumptions. Read them carefully before running any commands.
>
> 1. **Otto-factory is installed at `~/otto-factory`** (your home directory). If you put it somewhere else during installation, replace every `~/otto-factory` in the commands below with your actual path.
>
> 2. **You will need a GitHub repository that belongs to you.** The name `my-first-project` used throughout these steps is just an example — GitHub requires every repository name to be unique per account, so you need to create this repo yourself. You can name it anything you like, but you must use that exact same name in every command below. If you pick `awesome-webpage` instead of `my-first-project`, replace every occurrence of `my-first-project` in these steps with `awesome-webpage`.
>
> 3. **Replace `YOUR-USERNAME` with your actual GitHub username** everywhere it appears. You can find your username at [github.com](https://github.com) — it appears in the top-right corner when you are signed in.
>
> 4. **The GitHub CLI must be signed in.** Run `gh auth status` in your terminal. If it prints an error, run `gh auth login` and follow the prompts before continuing.
>
> 5. **The venv must be activated.** You will see `(venv)` at the start of your terminal prompt. If you do not see it, run `source ~/otto-factory/venv/bin/activate` (Mac/Linux) or `~/otto-factory/venv/Scripts/activate` (Windows) first.

### Step 1 — Create the project repo on GitHub

Go to [github.com/new](https://github.com/new) and create a new repository named `my-first-project` (or your chosen name).

**Important:** leave all "Initialize this repository" options **unchecked**. The repository must start completely empty — you will create the first commit yourself in Step 2, because Git requires at least one commit before branches can be created, and otto-factory's coder creates a new branch for each issue it works on.

### Step 2 — Clone it to your computer

Open a terminal and go to your home directory (not inside `otto-factory`):

```
cd ~
```

Clone your new repo — replace `YOUR-USERNAME` and `my-first-project` with your values:

```
git clone https://github.com/YOUR-USERNAME/my-first-project.git
```

Enter the project folder:

```
cd my-first-project
```

Create the required first commit. This does not add any files — it just gives git a starting point so branches can be created later:

```
git commit --allow-empty -m "init"
```

Push it to GitHub:

```
git push -u origin main
```

### Step 3 — Create the project config file

Otto-factory needs to know which GitHub repository to push code to. You tell it this by creating a `.otto` file in your project folder. This file is specific to this project and stays here permanently — think of it as the project's ID card for otto-factory.

Copy the template from otto-factory:

```bash
cp ~/otto-factory/.otto.example ~/my-first-project/.otto
```

Open `~/my-first-project/.otto` in a text editor (TextEdit on Mac, Notepad on Windows). You will see a file with comments explaining each line. Edit it to look like this, replacing `YOUR-USERNAME` with your GitHub username:

```ini
# Replace YOUR-USERNAME with your actual GitHub username (the same one you use to log in)
GITHUB_REPO=YOUR-USERNAME/my-first-project

# Leave this blank — the example project has no automated tests
TEST_COMMAND=

# The example project puts files at the root level, so use "." to stage everything
SOURCE_GLOB=.
```

Save the file. You do not need to reference it in any command — otto-factory reads it automatically when you run from this directory.

> **What is `SOURCE_GLOB` and why does it matter?**
> When the coder finishes writing files, it runs `git add` to stage them for a commit. `SOURCE_GLOB=.` means "stage everything in the project root." If your project keeps all its code in a `src/` subfolder, you would use `SOURCE_GLOB=src` so the coder only stages code files. For this first example, `.` is correct because the webpage files will be created right in the project root.

> **What about the `.env` file in otto-factory?**
> You created that during installation (`cp .env.example .env`). It controls machine-level settings like where `claude` and `gh` are installed. You do not need to change it for this walkthrough — the defaults work fine.

### Step 4 — Run the planner

Make sure the venv is active (you see `(venv)` in your prompt), then run the planner. The planner reads the example PRD and creates a GitHub Milestone with one Issue per feature, each written as a proper user story with acceptance criteria:

```bash
cd ~/my-first-project
python ~/otto-factory/main.py plan --prd ~/otto-factory/prd-example.md
```

Open your `my-first-project` repository on GitHub. Under the **Issues** tab you should see several new issues, and under **Milestones** you should see one called **Release 1**. Read through the issues — this is the plan the coder will follow. You can edit any issue before running the next step if you want to add detail or change scope.

### Step 5 — Run the full pipeline

Now start the automated loop. Otto-factory will work through every issue in the milestone — coding, testing, and reviewing each one in sequence:

```bash
cd ~/my-first-project
python ~/otto-factory/main.py run --milestone "Release 1"
```

Watch your terminal as the agents work. Open GitHub in a browser alongside it — you will see issues move through labels (`agent-in-progress`, `review-needed`) and Pull Requests appear and get merged in real time.

When the pipeline finishes, pull the completed code to your computer and open the result in your browser:

```bash
git pull
open index.html
```

### Bonus — trigger the reviewer manually

Once the pipeline has run and at least one PR exists, you can trigger the reviewer on it directly. This is useful when you want to re-review a PR after making manual edits, or when you want to understand what the reviewer looks at:

```bash
python ~/otto-factory/main.py review --pr 1
```

---

## Configuration reference

Settings are split across two files. You set each one up once and rarely need to touch them again.

### `otto-factory/.env` — machine-level config (one file for all projects)

This file lives inside the `otto-factory` folder. It contains settings that apply to every project on this machine — where the `claude` and `gh` programs are installed, and global timeout and retry defaults. You created it during installation by copying `.env.example`.

**You probably do not need to change anything here.** The defaults work for most setups. You only need to edit this file if:
- Otto-factory cannot find `claude` or `gh` — then set `CLAUDE_BIN` or `GH_BIN` to the full path returned by `which claude` or `which gh`
- Your test command uses a runtime managed by `nvm`, `pyenv`, or similar — then set `SHELL_INIT` to initialise it

| Setting | Default | What it does |
|---|---|---|
| `GH_BIN` | `gh` | Path to the GitHub CLI. Only change if `which gh` returns a non-standard path |
| `CLAUDE_BIN` | `claude` | Path to the Claude CLI. Only change if `which claude` returns a non-standard path |
| `CODER_TIMEOUT` | `600` | Seconds before the coder gives up on an issue (10 minutes). Increase for large tasks |
| `MAX_ATTEMPTS` | `3` | How many times the coder retries a failing issue before flagging it for your attention |
| `SHELL_INIT` | _(none)_ | Shell init command prepended to `TEST_COMMAND`. Needed only if your runtime is managed by `nvm`, `pyenv`, `asdf`, or similar |

### `<project>/.otto` — per-project config (one file per project)

This file lives inside your project folder. It tells otto-factory which GitHub repo to use and how to run your tests. You create it by copying `.otto.example` from the otto-factory folder into your project.

| Setting | Required? | What it does |
|---|---|---|
| `GITHUB_REPO` | **Yes** | Your GitHub repo in `owner/repo` format — e.g. `alice/my-project`. Full URL also works |
| `TEST_COMMAND` | No | Shell command to run your tests after each coding attempt. Leave blank to skip testing |
| `SOURCE_GLOB` | No (default: `src`) | The folder the coder stages when committing. Use `.` if files are at the root |

> `TARGET_DIR` no longer needs to be set. Otto-factory uses the directory you run from (or pass with `--project`) as the project root automatically.

### Per-project CLAUDE.md

Place a `CLAUDE.md` file in your project root to give the coder project-specific instructions — coding conventions, architecture notes, things to avoid, or anything else that should guide how it writes code. Claude Code picks this file up automatically when running in that directory.

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
├── .env.example            ← Machine-level config template (copy to .env)
├── .env                    ← Your machine-level config (tool paths, timeouts)
├── .otto.example           ← Per-project config template (copy into each project)
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

my-project/                 ← one folder per project you build
├── .otto                   ← Project config (GITHUB_REPO, TEST_COMMAND, …)
├── CLAUDE.md               ← Optional: coder instructions for this project
└── src/
```
