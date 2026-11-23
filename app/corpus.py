"""Original fictional support procedures for the capstone demonstration."""

DOCUMENTS = [
    {"id": "KB-NET-01", "title": "Office Wi-Fi and connectivity", "category": "network",
     "content": "Fictional RelayDesk procedure. For Wi-Fi, wireless, internet or ethernet connectivity problems: check whether other sites and devices can connect. Confirm Wi-Fi is enabled and connect to the known office SSID. Reconnect to that network once. Check the network status page if available. If the issue persists, provide the device model, office location, time and exact error to Network Support. Never connect to an unknown hotspot or share a Wi-Fi password in a ticket. An operator must approve any network configuration changes.",
     "steps": ["Check whether other sites and devices can connect.", "Confirm Wi-Fi is enabled and reconnect to the known office network once.", "Share the device model, location, time and exact error with Network Support."]},
    {"id": "KB-VPN-01", "title": "VPN connectivity and tunnel drops", "category": "vpn",
     "content": "Fictional RelayDesk procedure. For a VPN, remote-access tunnel or repeated VPN disconnection: check network connectivity before retrying the approved VPN client once. Check the displayed error and whether sign-in or MFA has expired. Record the client version, timestamp and error code. Forward persistent tunnel failures to Network Support. Do not disable the firewall, certificate checks, antivirus or MFA. Do not enter a password, token or recovery code into a support ticket.",
     "steps": ["Check network connectivity before retrying the approved VPN client once.", "Check whether sign-in or MFA has expired; never share codes in the ticket.", "Record the VPN client version, timestamp and error for Network Support."]},
    {"id": "KB-ACC-01", "title": "Account access and MFA recovery", "category": "account",
     "content": "Fictional RelayDesk procedure. For a locked account, forgotten password, sign-in failure, expired credentials, authenticator or MFA issue: use the organization's known self-service recovery page, reached from an existing trusted bookmark. Do not follow an unfamiliar link from a message. If recovery fails, contact Identity Support through the established internal directory for identity verification. Never request, reveal or store passwords, one-time passcodes, recovery codes or access tokens. RelayDesk cannot unlock accounts or bypass MFA.",
     "steps": ["Open the known self-service recovery page from an existing trusted bookmark.", "If recovery fails, ask Identity Support to complete identity verification.", "Do not include passwords, one-time codes or recovery codes in a ticket."]},
    {"id": "KB-SOFT-01", "title": "Application crashes and approved installation", "category": "software",
     "content": "Fictional RelayDesk procedure. For an application crash, frozen app, software installation or license issue: save work if possible and restart the affected application once. Record the application name, version and exact error. For installation requests, use the approved internal software catalog; licensed applications require an operator to confirm entitlement. Forward persistent failures to Application Support. Never download an unofficial installer, run an unreviewed script or grant administrator access based on a chat response.",
     "steps": ["Save work if possible and restart the affected application once.", "Record the application name, version and exact error.", "Use the approved software catalog; ask Application Support to review persistent errors or entitlement."]},
    {"id": "KB-DEV-01", "title": "Device, display and printer troubleshooting", "category": "device",
     "content": "Fictional RelayDesk procedure. For a laptop, monitor, keyboard, printer or dock problem: check visible cable connections and power indicators without opening the device. For printers, record the printer name and displayed error; verify that the expected printer is selected. For display issues, confirm the selected input source and dock connection. Record the asset label and location for Device Support. If a device has smoke, sparks, a swollen battery or a burning smell, stop using it, avoid handling damaged parts and contact on-site safety staff through the established local process. Do not open or repair electrical equipment.",
     "steps": ["Check visible cable connections and power indicators without opening the device.", "Record the asset label, location and any displayed error.", "Ask Device Support to review the device; stop using equipment with smoke or battery damage."]},
]

for document in DOCUMENTS:
    document.update(trusted=True, synthetic=True)


SAMPLE_REPORTS = [
    ("VPN keeps dropping during video meetings", "Home office", "Alex Morgan", "vpn", "normal"),
    ("The office Wi-Fi has no internet on the second floor", "West wing · Floor 2", "Jordan Lee", "network", "high"),
    ("My account is locked after changing my phone for MFA", "Design studio", "Sam Rivera", "account", "normal"),
    ("The reception printer is offline and shows a paper error", "Reception", "Taylor Quinn", "device", "normal"),
]
