# Second Brain — Client Onboarding System

Andrew's Keep → Notion "second brain", packaged to **replicate onto a client's Mac**.

**There is no installer.** You copy the files into the folders below, then run the skills —
the skills do the live setup (Keep auth, label creation, Notion config, launchd). This README is
the reference card; the work is the skills.

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

mkdir -p ~/.claude/skills ~/.local/bin ~/printing-press/library/notion ~/.hammerspoon
cp -R skills/* ~/.claude/skills/
cp bin/norg ~/.local/bin/norg
ln -sf ~/.claude/skills/keep-organizer/scripts/keep_cli.py ~/.local/bin/keep
cp bin/notion-pp-cli ~/printing-press/library/notion/notion-pp-cli   # norg hard-codes this path
cp capture/init.lua ~/.hammerspoon/init.lua
cp -R autolabeller ~/second-brain-automation
chmod +x ~/.local/bin/norg ~/printing-press/library/notion/notion-pp-cli
grep -q '.local/bin' ~/.zshrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

Then: add the **Notion MCP connector** in Claude Code, and **restart Claude Code** so it loads the
7 new skills.

## 3. Run the skills, in order

1. **`/second-brain-keep`** — Keep auth (cookie → master token; the flaky step) + create labels.
2. **`/second-brain-notion`** — duplicate the published Notion template into the client's workspace
   + write `~/.config/freshie/config.json` (the isolation gate — points everything at the client's
   Notion, never Andrew's).
3. **Capture** — install the Keep PWA → `capture/detect-bundle-id.sh` → load `capture/extension/`
   unpacked in the browser → reload Hammerspoon.
4. **`~/second-brain-automation/install.sh`** — load the hourly auto-labeller (after the Keep token exists).
5. **`/second-brain-verify`** — the **isolation gate**: a routed task lands in the **client's** Notion,
   nothing in Andrew's. Not done until this is green.

---

## What's in here

| Folder | Contents | Lands at |
|--------|----------|----------|
| `skills/` | 7 skills (3 onboarding + keep-organizer / keep-router / notion-project-skill / process-interviewer) | `~/.claude/skills/` |
| `bin/` | `norg`, `notion-pp-cli` | `~/.local/bin/` + `~/printing-press/library/notion/` |
| `capture/` | Hammerspoon hotkey config + minimal-Keep MV3 extension | `~/.hammerspoon/` + browser |
| `autolabeller/` | hourly Keep auto-labeller (its own `install.sh` loads launchd) | `~/second-brain-automation/` |

The `keep` CLI ships inside `skills/keep-organizer/scripts/keep_cli.py` (symlinked to PATH above).
Secrets are never in this repo — the skills capture them at runtime.
