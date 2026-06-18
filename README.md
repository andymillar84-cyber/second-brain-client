# Second Brain — Client Onboarding System

Andrew's Keep → Notion "second brain", packaged to **replicate onto a client's Mac**.

**There is no installer.** You copy the files into the folders below, then run the skills —
the skills do the live setup (Keep auth, label creation, Notion config, launchd). This README is
the reference card; the work is the skills.

> 🤖 **Agent running a (test) install: read [`AGENT-RUNBOOK.md`](AGENT-RUNBOOK.md) FIRST.** It has the
> ordered phases, the DO/DO-NOT guardrails, the restart handoff, and the recording protocol
> (run-log + debug docs to `/Users/Shared/sb-test-logs/`). This README is the reference it points to.

---

## 1. Supporting software (install first)

```bash
# Homebrew (skip if `which brew` already works):
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/opt/homebrew/bin/brew shellenv)"

brew install python uv
brew install --cask hammerspoon microsoft-edge   # any Chromium browser; NOT Safari
```
Plus **Claude Code**, signed into the client's own **paid** Claude account. (`gkeepapi` /
`gpsoauth` are auto-fetched by `uv` at runtime — no manual install.)

## 2. Copy the files

```bash
git clone https://github.com/andymillar84-cyber/second-brain-client.git
cd second-brain-client

mkdir -p ~/.claude/skills ~/.local/bin ~/.hammerspoon
cp -R skills/* ~/.claude/skills/
ln -sf ~/.claude/skills/keep-organizer/scripts/keep_cli.py ~/.local/bin/keep
cp capture/init.lua ~/.hammerspoon/init.lua
cp -R autolabeller ~/second-brain-automation
grep -q '.local/bin' ~/.zshrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

Then: install the **superpowers** plugin (`claude plugin install superpowers@claude-plugins-official`, or
via `/plugin`), add the **Notion MCP connector** (signed into the client's own Notion — this is the only
Notion auth there is), and **restart Claude Code** so it loads the 7 skills + superpowers.
(`process-interviewer` is among the 7 skills — a dependency the Keep/Notion skills call.)

> **Notion is MCP-only.** There is no `norg`/`notion-pp-cli` binary and no `~/.config/freshie/config.json`.
> The skills talk to Notion through the connected MCP and resolve every database by name, so writes can
> only ever land in the workspace the client connected.

## 3. Run the skills, in order

1. **`/second-brain-keep`** — Keep auth (cookie → master token; the flaky step) + create labels.
2. **`/second-brain-notion`** — connect the client's Notion MCP + duplicate the published Notion
   template into their workspace. (Isolation is the MCP login — no config file to write.)
3. **Capture** — install the Keep PWA → `capture/detect-bundle-id.sh` → load `capture/extension/`
   unpacked in the browser → reload Hammerspoon.
4. **`~/second-brain-automation/install.sh`** — load the hourly auto-labeller (after the Keep token exists).
5. **`/second-brain-verify`** — end-to-end smoke test: a routed task lands in the **client's** Notion.
   Not done until this is green.

---

## What's in here

| Folder | Contents | Lands at |
|--------|----------|----------|
| `skills/` | 7 skills (3 onboarding + keep-organizer / keep-router / notion-project-skill / process-interviewer) | `~/.claude/skills/` |
| `capture/` | Hammerspoon hotkey config + minimal-Keep MV3 extension | `~/.hammerspoon/` + browser |
| `autolabeller/` | hourly Keep auto-labeller (its own `install.sh` loads launchd) | `~/second-brain-automation/` |

The `keep` CLI ships inside `skills/keep-organizer/scripts/keep_cli.py` (symlinked to PATH above).
Secrets are never in this repo — the skills capture them at runtime.
