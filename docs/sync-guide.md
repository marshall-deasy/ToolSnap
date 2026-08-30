# ToolSnap Sync — Step by Step

## One-Time Setup (already done)
- ADB installed (`winget install Google.PlatformTools`)
- USB Debugging enabled on tablet
- `tsdb_sync_adb.bat` saved somewhere accessible (e.g. Desktop or `C:\toolsnap_db\`)

---

## Every Time You Add New Tools

### 1. Capture tools on the tablet
Open ToolSnap → photograph and fill in each tool → Finalize.

### 2. Plug in the tablet
Connect via USB cable. Make sure the tablet is in **File Transfer** mode (check the USB notification on the tablet).

### 3. Run the sync script
Double-click `tsdb_sync_adb.bat`. It will:
- Detect the tablet automatically
- Pull only new session folders into `C:\toolsnap_db\imports\`
- Skip any sessions already synced

### 4. Import into the database
- Launch `run_toolsnap_db.bat` (or switch to the app if it's already open)
- Go to the **Import** tab
- Click **Scan & Import**
- Check the log — new tools show as `OK`, previously imported ones show as `SKIP`

### 5. Verify
Switch to the **Search** tab. Your new tools should appear with photos and attributes.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "No device found" | Check USB cable, enable USB Debugging, approve prompt on tablet |
| "ADB not found" | Open a new terminal, or reinstall: `winget install Google.PlatformTools` |
| Images show `[missing]` | Old MTP copies — delete `C:\toolsnap_db\imports\`, re-run the bat |
| JPEG errors in console | Same as above — MTP corrupts binaries, ADB copies are clean |
| Import says "already imported" | Delete `C:\toolsnap_db\toolsnap.db` and re-import for a clean slate |
| Tablet not in file transfer mode | Swipe down on tablet → tap USB notification → select File Transfer / MTP |
