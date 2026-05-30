root@localhost:/data/data/com.termux/files/home/Discord_Bot# python3.11 ./bot.py
Starting bot.py...                                              Imports OK
Config loaded: ['token', 'channel_id', 'ping_role_id', 'tiktok_usernames', 'check_interval_minutes', 'browser_executable_path', 'ms_token']                                                     Monitoring 2 accounts, interval=1min
2026-05-30 02:33:32 [WARNING] discord.client: PyNaCl is not installed, voice will NOT be supported                              2026-05-30 02:33:32 [WARNING] discord.client: davey is not installed, voice will NOT be supported
2026-05-30 02:33:32 [INFO] tiktok_bot: Calling bot.run()...
2026-05-30 02:33:32 WARNING  discord.ext.commands.bot Privileged message content intent is missing, commands may not work as expected.
2026-05-30 02:33:32 [WARNING] discord.ext.commands.bot: Privileged message content intent is missing, commands may not work as expected.
2026-05-30 02:33:32 INFO     discord.client logging in using static token
2026-05-30 02:33:32 [INFO] discord.client: logging in using static token
2026-05-30 02:33:33 INFO     discord.gateway Shard ID None has connected to Gateway (Session ID: 391953f28463c10bd4061de02a7af950).                                                             2026-05-30 02:33:33 [INFO] discord.gateway: Shard ID None has connected to Gateway (Session ID: 391953f28463c10bd4061de02a7af950).
2026-05-30 02:33:35 [INFO] tiktok_bot: Logged in as TikTokPing#5324 (ID: 1510000436776796412)
2026-05-30 02:33:35 [INFO] tiktok_bot: Browser: /usr/bin/chromium | Monitoring 2 account(s) every 1 min
2026-05-30 02:33:36 [INFO] tiktok_bot: Synced 18 slash command(s)
2026-05-30 02:33:36 [INFO] tiktok_bot: Running scheduled TikTok check...
2026-05-30 02:33:59 [INFO] tiktok_bot: Fetched video for @rixxy.femboy
2026-05-30 02:33:59 ERROR    discord.ext.tasks Unhandled exception in internal background task 'check_tiktok'.
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/dist-packages/discord/ext/tasks/__init__.py", line 247, in _loop
    await self.coro(*args, **kwargs)
  File "/data/data/com.termux/files/home/Discord_Bot/./bot.py", line 151, in check_tiktok
    embed = build_video_embed(username, video, footer=f"Video ID: {video.id}")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/Discord_Bot/./bot.py", line 93, in build_video_embed
    desc = video.desc[:200] if video.desc else "*No description*"
                               ^^^^^^^^^^
AttributeError: 'Video' object has no attribute 'desc'
2026-05-30 02:33:59 [ERROR] discord.ext.tasks: Unhandled exception in internal background task 'check_tiktok'.
Traceback (most recent call last):
  File "/usr/local/lib/python3.11/dist-packages/discord/ext/tasks/__init__.py", line 247, in _loop
    await self.coro(*args, **kwargs)
  File "/data/data/com.termux/files/home/Discord_Bot/./bot.py", line 151, in check_tiktok
    embed = build_video_embed(username, video, footer=f"Video ID: {video.id}")
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/Discord_Bot/./bot.py", line 93, in build_video_embed
    desc = video.desc[:200] if video.desc else "*No description*"
                               ^^^^^^^^^^
AttributeError: 'Video' object has no attribute 'desc'
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
