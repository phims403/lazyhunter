# AI Bug Bounty Hunting Prompts

A prompt pack to run an **AI agent** (Claude Code, Command Code, OpenCode, etc.) as a **bug bounty hunter** that automatically hunts your targets exhaustively.

## Folder Contents

| File | Purpose |
|------|---------|
| `SUPER_PROMPT_BUG_BOUNTY_AI.md` | **Main prompt** — the complete hunting manual (methodology, tool rules, validation, output structure). This is what the goal prompts reference. |
| `goal-prompt.txt` | **First-session goal prompt** — to start a new hunt on a target. |
| `goal-prompt-continue-session.txt` | **Continuation goal prompt** — to resume an ongoing hunt (can be reused in new AI sessions). |

---

## How to Use

### 1. Scan the Target with LazyHunter First

Before using the AI, you **must** run LazyHunter on the target you want to hunt:

```bash
python lazyhunter.py -dps -t target.com -s fast
```

> **Deep Scan (`-dps`) is recommended** because it produces the most complete data: subdomains, active hosts, crawled URLs, params, JS files, sensitive data, nuclei results, and takeover — everything the AI needs as an attack surface.

The output is stored in a folder like:
```
target_output/target.com/
├── subdomains.txt
├── active.txt
├── crawled_filtered.txt
├── param.txt
├── js.txt
├── nuc_active.txt / nuc_exp.txt / nuc_dast.txt
├── 200_sens.txt / 403_sens.txt
└── ...
```
(or per-type folders such as `subdomain/`, `active/`, `crawled_filtered/` etc. if using `by_type` mode).

### 2. Pick an AI Agent

An AI agent with a **`/goal`** feature (autonomous loop mode), e.g. **Command Code**, is recommended. Other agents like Claude Code / OpenCode also work, but the `/goal` feature keeps the AI working until the target is achieved without stopping.

### 3. Open the Goal Prompt & Adjust the Paths

Open `goal-prompt.txt` (for the first session) in an editor, then change **2 parts**:

**a) First line — path to the main prompt:**

```
/goal @/home/phims/lazyhunter-update/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
```

Change the path to match where the prompt folder lives on your machine. Examples:
```
/goal @/home/user/lazyhunter-update/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
/goal @/Users/user/lazyhunter/update/prompt/SUPER_PROMPT_BUG_BOUNTY_AI.md
```

**b) Bottom section — target & LazyHunter output:**

```
*TARGET: change-this-to-your-target-domain.com
@(mention directory/file output lazyhunter)
```

- Replace `*TARGET` with the domain you want to hunt (e.g. `example.com`).
- Replace the `@(mention ...)` part with a **mention of the LazyHunter output folder** for that target, for example:
  ```
  @/home/user/lazyhunter/target_output/example.com
  ```
  or mention several files at once:
  ```
  @/home/user/lazyhunter/target_output/example.com/subdomains.txt
  @/home/user/lazyhunter/target_output/example.com/param.txt
  ```

### 4. Run It

Paste the whole adjusted goal prompt into the AI agent (or save it as a file and run `/goal @file`), then press Enter. The AI will:
1. Read the main prompt (the hunting manual).
2. Read all the LazyHunter output files from the mentioned folder.
3. Create a workspace folder `prompt-engineering-{model}-{timestamp}/`.
4. Hunt exhaustively until the goal (50 critical vulnerabilities) is reached or the session ends.

### 5. Continue a Previous Session

There are two ways to resume / continue hunting in the AI agent:

**Option A — easiest:** if your AI session is still open (you just hit a turn limit), simply type `continue` (or `/goal continue` in Command Code) to keep the AI working. The agent will pick up where it left off in the **same** session.

**Option B — new session, same target:** use `goal-prompt-continue-session.txt` when you **already finished one hunting session** and want to start a **fresh session** on the **same target** — for example because the previous session reached its goal (or ended), and you now want the AI to keep hunting that same domain.

1. Open `goal-prompt-continue-session.txt`.
2. Adjust the **main prompt path** (first line) and the **target + output folder** (bottom section) — the **target must be the same** as the previous session.
3. Run it in a new AI session.

The AI will automatically:
- Look for previous workspace folders (`prompt-engineering-*`) with the same target.
- Read `super-report.md` and `hunting_log_endpoints_tested.txt` from those sessions.
- **Continue hunting** — no restart from scratch, no re-reporting vulnerabilities that already exist (anti-duplication).

---

## AI Model Tips

- **`deepseek-v4-flash` is recommended** (or its flash variants) — it's already good at bug bounty tasks like this but **cheap**, making it ideal for long, repeated autonomous sessions.
- Larger models can be used for complex targets, but the cost is much higher because hunting sessions can be very long.

---

## Disclaimer

Only use this tool and these prompts on targets **you own** or that **explicitly allow** testing (bug bounty programs). Misuse for illegal activity is outside the tool owner's responsibility.
