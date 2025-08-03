# RG35XXSP-CUSTOM-MINUI-PAKS: PortMaster & Custom Drastic SDL port

This project brings two major enhancements to the **RG35XXSP running MinUI**:

1. **PortMaster Support** — Easily install and manage ports.
2. **Improved DS Emulation** — Adds a working Drastic SDL build with better layouts!

The work is based on a fork of [RGXX-Custom-MinUI-Paks](https://github.com/ryanmsartor/RGXX-Custom-MinUI-Paks), with contributions and enhancements tailored specifically for the **RG35XXSP**.

> ⚠️ While these enhancements were made for the RG35XXSP, they *may* work on other H700 devices (RG35XX+, RG35XXH), but this is **untested**. If you own one of these devices and can test, please let me know!

---

## 📦 Additions

- `PortMaster.pak` — Launches PortMaster to install ports.
- `AddPorts.pak` — Syncs installed ports into MinUI's Tools section.
- `Drastic DS Emulator` — Via SDL-based port.
- `wifi.pak` — Add WiFi setup capabilities from within MinUI (can be temperamental).
- Supporting files in `Roms/APPS/` to enable PortMaster.

---

## 📁 Installation Instructions

To install the included PAKs and supporting files:

1. **Copy the following folders from the .zip file in releases to the root of your MinUI SD card**:
    - `Emus/`
    - `Roms/`
    - `Tools/`

   > Choose **merge** if prompted. Do not delete existing folders.

2. **Add your ROMs** into the appropriate subfolders within `Roms/`.

3. **Safely eject the SD card and insert it into your RG35XXSP**.

---

## 🌐 Connecting to WiFi

PortMaster requires internet access. You can connect to WiFi in one of two ways:

### Method 1: Using Stock OS (More Reliable)

1. In MinUI, go to **Tools > Reboot into Stock**.
2. Once in Stock OS, connect to your WiFi as normal.
3. Navigate to **Apps > TF2** and select **Reboot into MinUI**.
4. Perform a **full reboot**.

### Method 2: Using `wifi.pak` in MinUI (Experimental)

1. In MinUI, go to **Tools > wifi**.
2. Attempt to connect via the built-in interface.
3. After connecting, perform a **full reboot**.

---

## 🚀 Using PortMaster

1. Ensure WiFi is working (there should be a wifi symbol next to the battery indicator).
2. Go to **Tools > PortMaster** and launch it.
3. When prompted:
    - Select **Yes** to update PortMaster.
    - Select **Yes** to install PortMaster runtimes.

   > ⏳ The runtime installation can take up to **25 minutes** depending on your internet. If you get an error after the 28th download, that's normal — PortMaster should still work.

4. Once done, you’ll be inside the PortMaster interface.
5. From here, install a game like **Apotris** under "Ready to Run Ports".
6. Exit PortMaster.

---

## ➕ Adding Installed Ports to MinUI

1. Go to **Tools > AddPorts**.
2. This will scan for new ports installed by PortMaster and add them as launchable entries in the Tools menu.
3. Example: After installing Apotris and launching AddPorts, a new **Apotris** entry will appear in **Tools**.

---

## 🕹️ Hotkeys

### PortMaster Ports
- **Menu + Start**: Exit the port/game.

### Drastic DS Emulator
> Default hotkey modifier is the **Menu** button (can be changed in settings).

| Combo                 | Action                              |
|----------------------|-------------------------------------|
| Hotkey + Left/Right  | Change display mode/layouts         |
| Hotkey + Up/Down     | Change touch cursor screen          |
| Hotkey + B           | Toggle pixel/blur                   |
| Hotkey + Y           | Change theme                        |
| Hotkey + Select      | Open original Drastic settings menu |
| Hotkey + Start       | Open custom settings screen         |
| Hotkey + R1          | Fast Forward                        |
| Hotkey + L1          | Exit Emulator                       |
| L2                   | Show touch cursor                   |
| R2                   | Swap screens                        |
| Left Analog          | Move touch cursor                   |
| R3                   | Simulate touch press                |

---

## 🐛 Notes and Tips

- **Stardew Valley** works! Be sure to use the **32-bit version from Steam**.
- If Stardew’s UI scaling is off:
    1. Wait until the main menu loads.
    2. Hover over **Load**.
    3. Press **Up**, then **Right**, then **A**.
    4. This should correct the scaling.
- Some ports may take longer to boot — this is normal.

---

## 🙏 Credits and Sources

Big thanks to the following repositories and developers whose work made this possible:

- [ryanmsartor/RGXX-Custom-MinUI-Paks](https://github.com/ryanmsartor/RGXX-Custom-MinUI-Paks)
- [cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification](https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification)
- [trngaje/rg35xxh_binary (Drastic SDL Port)](https://github.com/trngaje/rg35xxh_binary/tree/master/minui)
- [josegonzalez/minui-wifi-pak](https://github.com/josegonzalez/minui-wifi-pak)

---

## 📫 Feedback & Testing

If you own an RG35XX+, H, or other H700 device and can test these enhancements, please let me know by opening an issue or PR. I'd love to confirm compatibility!

---
