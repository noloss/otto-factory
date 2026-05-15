# PRD: otto-factory Landing Page

## Goal

Build a single-page static website that explains what otto-factory is, why someone would want to use it, and how to get started. The page should be visually appealing, work without any backend or build tools, and be deployable by simply opening `index.html` in a browser.

## Target audience

Product managers and non-technical founders who have a Claude Pro or Max subscription and want to build software without hiring developers.

## Pages and sections

The website is a single `index.html` file with inline CSS and JavaScript. No frameworks, no npm, no build step.

### Hero section
- Large headline: "Turn your Claude subscription into a software factory"
- Subheadline: "Describe what you want to build. otto-factory writes the code, tests it, and reviews it — automatically."
- A single call-to-action button: "Get started on GitHub" linking to `#get-started`

### How it works section
- Section heading: "How it works"
- Three steps displayed as a visual flow (cards or numbered steps):
  1. **Write a PRD** — Describe your product in plain English
  2. **Run the planner** — otto-factory creates GitHub Issues from your requirements
  3. **Watch it build** — Three AI agents write, test, and review the code in a loop
- Each step has a short one-sentence description

### Why otto-factory section
- Section heading: "No API key required"
- Two columns or cards comparing the two approaches:
  - **Other AI coding tools**: Require an Anthropic API key. Usage-based billing. Costs add up fast.
  - **otto-factory**: Runs on your Claude Pro or Max subscription. No API key. No per-token charges.
- A note explaining that GitHub Issues are used as the state machine, making every step of the process visible and human-readable

### Get started section
- Section heading: "Get started"
- A short numbered list of the first steps (clone, configure, run)
- A code block showing the two key commands:
  ```
  python main.py plan --prd prd.md
  python main.py run --milestone "Release 1"
  ```
- A link to the GitHub repository README for full instructions

### Footer
- Simple footer with the project name and a link to the GitHub repository

## Design requirements

- Clean, modern look with a dark background (e.g. `#0d1117`, GitHub's dark theme colour) and white text
- Accent colour: a bright teal or blue (e.g. `#58a6ff`)
- Readable body font — use the system font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`)
- Responsive: must look good on both desktop and mobile screens
- No external dependencies — no CDN links, no Google Fonts, no JavaScript libraries

## Acceptance criteria

**Hero section**
- Given a user opens index.html in a browser, when the page loads, then a headline containing the words "Claude subscription" and "software factory" is visible above the fold

**How it works**
- Given the page is loaded, when the user scrolls to the how-it-works section, then three clearly numbered steps are visible with headings and descriptions

**Comparison section**
- Given the page is loaded, when the user reads the comparison section, then both "API key" and "Claude Pro or Max subscription" appear as distinct options with different styling to highlight the contrast

**Get started section**
- Given the page is loaded, when the user clicks the "Get started on GitHub" button, then the page scrolls to the get-started section

**Responsive layout**
- Given a user opens the page on a mobile device (screen width under 600px), when the page loads, then all sections are readable and no content overflows horizontally

**No external dependencies**
- Given the page's source code is inspected, when checking for external resource links, then no CDN, Google Fonts, or external JavaScript sources are present

**Deployability**
- Given the repository contains only index.html, when a user opens that file directly in a browser, then the full page renders correctly without a web server
