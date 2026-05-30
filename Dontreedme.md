root@localhost:/data/data/com.termux/files/home/Discord_Bot# python3.11 ./bot.py
Starting bot.py...                                              Imports OK
Config loaded: ['token', 'channel_id', 'ping_role_id', 'tiktok_usernames', 'check_interval_minutes', 'browser_executable_path', 'ms_token']
Monitoring 2 accounts, interval=1min                            2026-05-30 02:25:15 [WARNING] discord.client: PyNaCl is not installed, voice will NOT be supported
2026-05-30 02:25:15 [WARNING] discord.client: davey is not installed, voice will NOT be supported                               2026-05-30 02:25:15 [INFO] tiktok_bot: Calling bot.run()...
2026-05-30 02:25:15 WARNING  discord.ext.commands.bot Privileged message content intent is missing, commands may not work as expected.                                                          2026-05-30 02:25:15 [WARNING] discord.ext.commands.bot: Privileged message content intent is missing, commands may not work as expected.                                                        2026-05-30 02:25:15 INFO     discord.client logging in using static token                                                       2026-05-30 02:25:15 [INFO] discord.client: logging in using static token
2026-05-30 02:25:16 INFO     discord.gateway Shard ID None has connected to Gateway (Session ID: 2b524ca7c3166c669ff8b9c7c80c28fd).                                                             2026-05-30 02:25:16 [INFO] discord.gateway: Shard ID None has connected to Gateway (Session ID: 2b524ca7c3166c669ff8b9c7c80c28fd).
2026-05-30 02:25:18 [INFO] tiktok_bot: Logged in as TikTokPing#5324 (ID: 1510000436776796412)
2026-05-30 02:25:18 [INFO] tiktok_bot: Browser: /usr/bin/chromium | Monitoring 2 account(s) every 1 min
s2026-05-30 02:25:59 [INFO] tiktok_bot: Synced 18 slash command(s)
2026-05-30 02:25:59 [INFO] tiktok_bot: Running scheduled TikTok check...
2026-05-30 02:26:01 [WARNING] tiktok_bot: Strategy {'headless': False, 'browser': 'chromium'} failed for @rixxy.femboy: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

╔════════════════════════════════════════════════════════════════════════════════════════════════╗
║ Looks like you launched a headed browser without having a XServer running.                     ║
║ Set either 'headless: true' or use 'xvfb-run <your-playwright-app>' before running Playwright. ║
║                                                                                                ║
║ <3 Playwright Team                                                                             ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
Call log:
  - <launching> /usr/bin/chromium --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-client-side-phishing-detection --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-edgeupdater --disable-extensions --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion --enable-features=CDPScreenshotNewSurface --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --edge-skip-compat-layer-relaunch --disable-infobars --disable-search-engine-choice-screen --disable-sync --enable-unsafe-swiftshader --no-sandbox --user-data-dir=/tmp/playwright_chromiumdev_profile-v3Fuer --remote-debugging-pipe --no-startup-window
  - <launched> pid=14345
  - [pid=14345][err] [14345:14372:0530/022601.594788:ERROR:dbus/bus.cc:405] Failed to connect to the bus: Failed to connect to socket /run/dbus/system_bus_socket: No such file or directory
  - [pid=14345][err] [14345:14345:0530/022601.604233:ERROR:ui/ozone/platform/x11/ozone_platform_x11.cc:257] Missing X server or $DISPLAY
  - [pid=14345][err] [14345:14345:0530/022601.604271:ERROR:ui/aura/env.cc:246] The platform failed to initialize.  Exiting.
  - [pid=14345] <gracefully close start>
  - [pid=14345] <kill>
  - [pid=14345] <will force kill>
  - [pid=14345] <process did exit: exitCode=1, signal=null>
  - [pid=14345] starting temporary directories cleanup
  - [pid=14345] finished temporary directories cleanup
  - [pid=14345] <gracefully close end>

2026-05-30 02:26:03 [WARNING] tiktok_bot: Strategy {'headless': False, 'browser': 'webkit'} failed for @rixxy.femboy: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /usr/bin/chromium --inspector-pipe --no-startup-window
<launched> pid=14393
[pid=14393][err] [14393:14393:0530/022603.013118:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
Call log:
  - <launching> /usr/bin/chromium --inspector-pipe --no-startup-window
  - <launched> pid=14393
  - [pid=14393][err] [14393:14393:0530/022603.013118:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
  - [pid=14393] <gracefully close start>
  - [pid=14393] <kill>
  - [pid=14393] <will force kill>
  - [pid=14393] <process did exit: exitCode=1, signal=null>
  - [pid=14393] starting temporary directories cleanup
  - [pid=14393] finished temporary directories cleanup
  - [pid=14393] <gracefully close end>

2026-05-30 02:26:04 [WARNING] tiktok_bot: Strategy {'headless': True, 'browser': 'webkit'} failed for @rixxy.femboy: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /usr/bin/chromium --inspector-pipe --headless --no-startup-window
<launched> pid=14426
[pid=14426][err] [14426:14426:0530/022604.754579:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
Call log:
  - <launching> /usr/bin/chromium --inspector-pipe --headless --no-startup-window
  - <launched> pid=14426
  - [pid=14426][err] [14426:14426:0530/022604.754579:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
  - [pid=14426] <gracefully close start>
  - [pid=14426] <kill>
  - [pid=14426] <will force kill>
  - [pid=14426] <process did exit: exitCode=1, signal=null>
  - [pid=14426] starting temporary directories cleanup
  - [pid=14426] finished temporary directories cleanup
  - [pid=14426] <gracefully close end>

2026-05-30 02:26:04 [ERROR] tiktok_bot: All strategies failed for @rixxy.femboy
2026-05-30 02:26:06 [WARNING] tiktok_bot: Strategy {'headless': False, 'browser': 'chromium'} failed for @boo_softboi: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

╔════════════════════════════════════════════════════════════════════════════════════════════════╗
║ Looks like you launched a headed browser without having a XServer running.                     ║
║ Set either 'headless: true' or use 'xvfb-run <your-playwright-app>' before running Playwright. ║
║                                                                                                ║
║ <3 Playwright Team                                                                             ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
Call log:
  - <launching> /usr/bin/chromium --disable-field-trial-config --disable-background-networking --disable-background-timer-throttling --disable-backgrounding-occluded-windows --disable-back-forward-cache --disable-breakpad --disable-client-side-phishing-detection --disable-component-extensions-with-background-pages --disable-component-update --no-default-browser-check --disable-default-apps --disable-dev-shm-usage --disable-edgeupdater --disable-extensions --disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,BoundaryEventDispatchTracksNodeRemoval,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate,AutoDeElevate,RenderDocument,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion --enable-features=CDPScreenshotNewSurface --allow-pre-commit-input --disable-hang-monitor --disable-ipc-flooding-protection --disable-popup-blocking --disable-prompt-on-repost --disable-renderer-backgrounding --force-color-profile=srgb --metrics-recording-only --no-first-run --password-store=basic --use-mock-keychain --no-service-autorun --export-tagged-pdf --disable-search-engine-choice-screen --unsafely-disable-devtools-self-xss-warnings --edge-skip-compat-layer-relaunch --disable-infobars --disable-search-engine-choice-screen --disable-sync --enable-unsafe-swiftshader --no-sandbox --user-data-dir=/tmp/playwright_chromiumdev_profile-yRuvQ9 --remote-debugging-pipe --no-startup-window
  - <launched> pid=14460
  - [pid=14460][err] [14460:14487:0530/022606.376446:ERROR:dbus/bus.cc:405] Failed to connect to the bus: Failed to connect to socket /run/dbus/system_bus_socket: No such file or directory
  - [pid=14460][err] [14460:14460:0530/022606.383849:ERROR:ui/ozone/platform/x11/ozone_platform_x11.cc:257] Missing X server or $DISPLAY
  - [pid=14460][err] [14460:14460:0530/022606.383888:ERROR:ui/aura/env.cc:246] The platform failed to initialize.  Exiting.
  - [pid=14460] <gracefully close start>
  - [pid=14460] <kill>
  - [pid=14460] <will force kill>
  - [pid=14460] <process did exit: exitCode=1, signal=null>
  - [pid=14460] starting temporary directories cleanup
  - [pid=14460] finished temporary directories cleanup
  - [pid=14460] <gracefully close end>

2026-05-30 02:26:07 [WARNING] tiktok_bot: Strategy {'headless': False, 'browser': 'webkit'} failed for @boo_softboi: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /usr/bin/chromium --inspector-pipe --no-startup-window
<launched> pid=14508
[pid=14508][err] [14508:14508:0530/022607.815489:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
Call log:
  - <launching> /usr/bin/chromium --inspector-pipe --no-startup-window
  - <launched> pid=14508
  - [pid=14508][err] [14508:14508:0530/022607.815489:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
  - [pid=14508] <gracefully close start>
  - [pid=14508] <kill>
  - [pid=14508] <will force kill>
  - [pid=14508] <process did exit: exitCode=1, signal=null>
  - [pid=14508] starting temporary directories cleanup
  - [pid=14508] finished temporary directories cleanup
  - [pid=14508] <gracefully close end>

2026-05-30 02:26:09 [WARNING] tiktok_bot: Strategy {'headless': True, 'browser': 'webkit'} failed for @boo_softboi: BrowserType.launch: Target page, context or browser has been closed
Browser logs:

<launching> /usr/bin/chromium --inspector-pipe --headless --no-startup-window
<launched> pid=14541
[pid=14541][err] [14541:14541:0530/022609.525316:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
Call log:
  - <launching> /usr/bin/chromium --inspector-pipe --headless --no-startup-window
  - <launched> pid=14541
  - [pid=14541][err] [14541:14541:0530/022609.525316:ERROR:content/browser/zygote_host/zygote_host_impl_linux.cc:101] Running as root without --no-sandbox is not supported. See https://crbug.com/638180.
  - [pid=14541] <gracefully close start>
  - [pid=14541] <kill>
  - [pid=14541] <will force kill>
  - [pid=14541] <process did exit: exitCode=1, signal=null>
  - [pid=14541] starting temporary directories cleanup
  - [pid=14541] finished temporary directories cleanup
  - [pid=14541] <gracefully close end>

2026-05-30 02:26:09 [ERROR] tiktok_bot: All strategies failed for @boo_softboi
