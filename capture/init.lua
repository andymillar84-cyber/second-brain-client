-- Hammerspoon config: Keep instant-capture hotkey
--   ⌃ ⌃  (double-tap left Control) → Google Keep PWA, fullscreen, new-note ready
-- Pure Hammerspoon (no Karabiner): one process, one Accessibility grant.
--
-- The Keep PWA's bundle ID is per-install, so it is NOT hardcoded here — it is
-- read from ~/.hammerspoon/keep_bundle_id.txt, which detect-bundle-id.sh writes.
-- Run that script once (after installing the Keep PWA) before reloading.

require("hs.ipc")
hs.ipc.cliInstall()

local logger = hs.logger.new("keepcapture", "info")

-- Modifier keycodes
local LEFT_CONTROL = 0x3B

-- Tap timing
local HOLD_THRESHOLD = 0.25
local DOUBLE_WINDOW  = 0.40

-- Shared state (the toggle remembers the app it pulled focus from)
local lastFrontPidByBundle = {}

-- Read the Keep PWA bundle ID written by detect-bundle-id.sh
local function readBundleID()
  local path = os.getenv("HOME") .. "/.hammerspoon/keep_bundle_id.txt"
  local f = io.open(path, "r")
  if not f then return nil end
  local id = (f:read("*l") or ""):gsub("%s+", "")
  f:close()
  if id == "" then return nil end
  return id
end

-- Returns the first window of an app, falling back from mainWindow to allWindows[1]
local function getAppWindow(app)
  return app:mainWindow() or app:allWindows()[1]
end

-- Send Escape + a key into the focused app, after a small delay
local function sendKey(keyChar, delay)
  hs.timer.doAfter(delay or 0.45, function()
    hs.eventtap.keyStroke({}, "escape", 80000)
    hs.eventtap.keyStroke({}, keyChar, 80000)
  end)
end

-- Drive an app into fullscreen with retry (window may not be ready immediately after activate)
local function ensureFullscreen(app, attemptsLeft, onDone)
  attemptsLeft = attemptsLeft or 4
  local w = getAppWindow(app)
  if w and w:isFullScreen() then
    if onDone then hs.timer.doAfter(0.25, onDone) end
    return
  end
  if attemptsLeft <= 0 then
    if onDone then onDone() end
    return
  end
  if w and not w:isFullScreen() then w:setFullScreen(true) end
  hs.timer.doAfter(0.4, function() ensureFullscreen(app, attemptsLeft - 1, onDone) end)
end

-- Build a toggle function for a specific app.
-- config: { bundleID, fullscreen (bool), onShow (fn(app, isColdLaunch) — optional) }
local function makeAppToggle(config)
  local bundleID = config.bundleID

  local function rememberFront()
    local front = hs.application.frontmostApplication()
    if front
      and front:bundleID() ~= "org.hammerspoon.Hammerspoon"
      and front:bundleID() ~= bundleID then
      lastFrontPidByBundle[bundleID] = front:pid()
    end
  end

  local function restoreFront()
    local pid = lastFrontPidByBundle[bundleID]
    if not pid then return end
    local app = hs.application.applicationForPID(pid)
    if app then app:activate(true) end
  end

  local function showAndPrep(app, isColdLaunch)
    app:activate(true)
    local startDelay = isColdLaunch and 1.5 or 0.2
    hs.timer.doAfter(startDelay, function()
      if config.fullscreen then
        ensureFullscreen(app, 4, function()
          if config.onShow then config.onShow(app, isColdLaunch) end
        end)
      else
        if config.onShow then config.onShow(app, isColdLaunch) end
      end
    end)
  end

  return function()
    logger.i("toggle invoked: " .. bundleID)
    local app = hs.application.get(bundleID)

    if not app then
      rememberFront()
      hs.application.open(bundleID, 5, true)
      hs.timer.doAfter(1.2, function()
        local a = hs.application.get(bundleID)
        if a then showAndPrep(a, true) end
      end)
      return
    end

    if app:isFrontmost() then
      app:hide()
      restoreFront()
    else
      rememberFront()
      showAndPrep(app, false)
    end
  end
end

-- Build a double-tap watcher on a specific modifier keycode.
-- onDoubleTap: zero-arg function to invoke when double-tap is detected.
-- Returns the started eventtap (caller should retain it).
local function makeDoubleTapBinding(keyCode, onDoubleTap)
  local state = { downAt = nil, firstTapAt = nil }
  local tap = hs.eventtap.new({hs.eventtap.event.types.flagsChanged}, function(e)
    if e:getKeyCode() ~= keyCode then return false end
    local now = hs.timer.absoluteTime() / 1e9
    local flags = e:getFlags()
    local modName
    if keyCode == LEFT_CONTROL then modName = "ctrl" end
    local isDown = flags[modName] == true
    if isDown then
      state.downAt = now
    else
      if state.downAt then
        local held = now - state.downAt
        state.downAt = nil
        if held < HOLD_THRESHOLD then
          if state.firstTapAt and (now - state.firstTapAt) < DOUBLE_WINDOW then
            state.firstTapAt = nil
            onDoubleTap()
          else
            state.firstTapAt = now
          end
        else
          state.firstTapAt = nil
        end
      end
    end
    return false
  end)
  tap:start()
  return tap
end

-- ─── Keep hotkey ──────────────────────────────────────────────────────────────
local keepBundle = readBundleID()

if not keepBundle then
  hs.alert.show("Keep capture: bundle ID not set — run detect-bundle-id.sh, then reload", 5)
  logger.w("keep_bundle_id.txt missing or empty; hotkey not bound")
else
  _G.keep = {}
  _G.keep.toggle = makeAppToggle({
    bundleID = keepBundle,
    fullscreen = true,
    onShow = function(app, isColdLaunch)
      -- Press `c` to open a new-note modal in Keep
      sendKey("c", isColdLaunch and 1.5 or 0.45)
    end,
  })
  _G.keep.tap = makeDoubleTapBinding(LEFT_CONTROL, _G.keep.toggle)
end

-- ─── Startup ──────────────────────────────────────────────────────────────────
if not hs.accessibilityState() then
  logger.w("Hammerspoon lacks Accessibility — prompting")
  hs.accessibilityState(true)
end

hs.autoLaunch(true)
hs.dockIcon(false)  -- hide from dock; menubar tray icon stays for console access

-- Pre-launch Keep PWA hidden so the first toggle is instant
if keepBundle then
  hs.timer.doAfter(4, function()
    if not hs.application.get(keepBundle) then
      logger.i("Pre-launching Keep PWA on Hammerspoon startup")
      hs.application.open(keepBundle, 5, true)
      hs.timer.doAfter(1.0, function()
        local a = hs.application.get(keepBundle)
        if a then a:hide() end
      end)
    end
  end)
end

-- Auto-reload on init.lua edit
_G.configWatcher = hs.pathwatcher.new(os.getenv("HOME") .. "/.hammerspoon/", function(files)
  for _, f in ipairs(files) do
    if f:sub(-4) == ".lua" then
      hs.reload()
      return
    end
  end
end):start()

if keepBundle then
  hs.alert.show("Hammerspoon ready · ⌃⌃ Keep", 1.5)
end
