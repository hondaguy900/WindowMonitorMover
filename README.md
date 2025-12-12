# Window Monitor Mover

Automatically move application windows to specified monitors on startup or when they're launched. Perfect for multi-monitor setups where you want specific applications to always open on designated screens.

## Features

### Core Functionality
- **Automatic Window Placement**: Set rules to move specific applications to designated monitors
- **Real-Time Monitoring**: Continuously monitors for new windows and moves them automatically
- **Window Size Control**: Choose to maximize, minimize, or keep normal size after moving
- **Visual Rule Configuration**: Drag the configuration window to your target monitor to set rules
- **System Tray Support**: Minimize to tray and control monitoring from the system tray
- **Auto-Start**: Automatically begins monitoring when rules are configured
- **Persistent Rules**: Rules are saved and loaded automatically between sessions

### Advanced Features
- **Process Detection**: Lists all running applications with windows for easy selection
- **Multiple Rules**: Create unlimited rules for different applications
- **Smart Detection**: Only moves windows once to prevent repeated relocations
- **Activity Logging**: Real-time log of all window movements and monitoring activity
- **Visual Status Indicators**: Green/red icons in tray and taskbar show monitoring status
- **Monitor Identification**: App assigns consistent monitor numbers for reliable targeting

## Installation

### Prerequisites
- Python 3.7 or higher
- Windows OS (uses Windows-specific APIs)
- pip package manager

### Required Packages
```bash
pip install psutil pywin32
```

### Optional Packages (for system tray support)
```bash
pip install pystray pillow
```

### Download
```bash
git clone https://github.com/Hondaguy900/WindowMonitorMover.git
cd WindowMonitorMover
```

## Usage

### Quick Start

1. **Launch the application**:
```bash
   python window_mover.py
```

2. **Create your first rule**:
   - Click "➕ Add New Rule"
   - Select an application from the list or type its name
   - **DRAG the yellow dialog window** to your target monitor
   - Choose window size behavior (normal, maximized, or minimized)
   - Click "💾 Save Rule"

3. **Start monitoring**:
   - Click "▶ Start Monitoring" to activate all rules
   - The status indicator will turn green
   - New windows matching your rules will be automatically moved

4. **Monitor from system tray** (if pystray is installed):
   - Close the window to minimize to system tray
   - Double-click tray icon to restore window
   - Right-click tray icon for quick controls

### Creating Rules

The rule creation process uses a unique drag-to-target method:

1. **Select Process**: Choose from the list of running applications or manually type the process name (without .exe)
2. **Set Target Monitor**: Physically drag the yellow configuration window to the monitor you want the application to appear on
3. **Choose Window Size**:
   - **Keep Current Size**: Window maintains its original dimensions (default)
   - **Maximize After Moving**: Window is maximized on the target monitor
   - **Minimize After Moving**: Window is minimized after being moved
4. **Save**: The rule is saved and immediately available for monitoring

### Managing Rules

- **Edit Rule**: Select a rule and click "✏️ Edit Selected" to modify it
- **Remove Rule**: Select a rule and click "🗑️ Remove Selected" to delete it
- **Restart Monitoring**: Click "🔄 Restart Monitoring" after making changes to active rules

### System Tray Features

When pystray and PIL are installed:
- **Color-Coded Icons**: 
  - 🔴 Red: Monitoring stopped
  - 🟢 Green: Monitoring active
- **Quick Access**: Double-click tray icon to show/hide main window
- **Tray Menu**: Right-click for start/stop controls and exit option
- **Notifications**: Shows notification when minimized to tray

## Configuration

### Config File
Rules are automatically saved to `window_mover_config.json` in the application directory.

### Example Configuration
```json
[
  {
    "process": "chrome",
    "monitor": {
      "left": 1920,
      "top": 0,
      "right": 3840,
      "bottom": 1080,
      "is_primary": false
    },
    "size": "maximized"
  },
  {
    "process": "Spotify",
    "monitor": {
      "left": 0,
      "top": 0,
      "right": 1920,
      "bottom": 1080,
      "is_primary": true
    },
    "size": "normal"
  }
]
```

## Use Cases

### Example 1: Development Workstation
Set up your development environment to automatically organize:
- **IDE** → Main monitor (maximized)
- **Browser** → Secondary monitor (maximized)
- **Slack/Teams** → Third monitor (normal)
- **Music Player** → Third monitor (minimized)

### Example 2: Trading/Finance Setup
Configure financial applications for instant access:
- **Trading Platform** → Primary monitor (maximized)
- **Market Charts** → Secondary monitor (maximized)
- **News Feed** → Third monitor (normal)

### Example 3: Content Creation
Organize creative tools efficiently:
- **Video Editor** → Primary monitor (maximized)
- **Asset Browser** → Secondary monitor (normal)
- **Preview Window** → Third monitor (maximized)

## Technical Details

### Built With
- **Python 3.x**: Core programming language
- **Tkinter**: GUI framework (included with Python)
- **psutil**: Process and system utilities
- **pywin32**: Windows API access for window manipulation
- **pystray** (optional): System tray integration
- **PIL/Pillow** (optional): Icon generation for tray

### How It Works

1. **Monitor Detection**: Uses Windows API to enumerate all connected monitors and their positions
2. **Process Monitoring**: Continuously scans for running processes matching configured rules
3. **Window Detection**: Identifies top-level windows for matched processes
4. **Window Movement**: Uses Windows API to reposition windows to target monitor coordinates
5. **Size Application**: Applies maximized, minimized, or normal state after moving
6. **Tracking**: Maintains a set of moved windows to prevent repeated relocations

### Monitor Numbering

The application assigns monitor numbers based on:
1. **Primary Monitor**: Always Monitor 1
2. **Secondary Monitors**: Numbered by position (left-to-right, top-to-bottom)

**Note**: These numbers may differ from Windows Display Settings numbering.

### Performance Considerations

- **Polling Interval**: Checks for new windows every 0.5 seconds
- **Memory Usage**: Minimal - tracks only window handles of moved windows
- **CPU Usage**: Very low - event-driven with short sleep intervals
- **Startup Impact**: Auto-starts monitoring only if rules exist

## Troubleshooting

### Common Issues

**"Application not moving windows"**
- Ensure monitoring is started (green status indicator)
- Verify the process name matches exactly (without .exe)
- Check that the application creates top-level windows
- Some applications create windows under different process names

**"System tray not working"**
- Install optional dependencies: `pip install pystray pillow`
- Restart the application after installing dependencies
- Check for error messages in the activity log

**"Monitor numbers seem wrong"**
- Monitor numbers are assigned by this app, not Windows
- The primary monitor is always Monitor 1
- Drag the configuration dialog to verify the correct monitor
- Monitor numbers are based on physical position relative to primary

**"Windows keep getting moved repeatedly"**
- This should not happen - moved windows are tracked
- Try clicking "🔄 Restart Monitoring" to reset tracking
- Check for duplicate rules for the same process

**"Application crashes on startup"**
- Ensure pywin32 is properly installed: `python -m pip install --upgrade pywin32`
- Try running as administrator if permission errors occur
- Check that window_mover_config.json is valid JSON

## Version History

### Current Version
- Full window size control (normal, maximized, minimized)
- Drag-to-target monitor configuration
- System tray integration with color-coded status
- Auto-start monitoring when rules exist
- Smart window state detection and restoration
- Taskbar icon color indicators
- Improved window detection and movement logic

## Credits

**Developer**: Hondaguy900  
**AI Assistant**: Claude (Anthropic)

Developed to solve the common frustration of applications opening on the wrong monitor in multi-monitor setups. Built with extensive collaboration between human expertise and AI assistance.

## License

This project is available for use under standard open-source practices. Feel free to modify and distribute with attribution.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

### Potential Enhancements
- Support for window position within monitor (e.g., left half, right half)
- Profile system for different monitor configurations (office vs. home)
- Command-line interface for scripted control
- Window size templates (specific dimensions)
- Hotkey support for manual window movement
- Remember last window size/position per application
- Multi-rule support (different rules for different window titles from same process)
- Delay option before moving (for applications that reposition themselves)

## Known Limitations

- **Windows Only**: Uses Windows-specific APIs (win32gui, win32con)
- **Top-Level Windows Only**: Doesn't move child windows or dialogs
- **Process Name Based**: Cannot distinguish between multiple windows from the same process with different titles (use case: multiple Chrome profiles)
- **Some Applications Resist**: Certain applications (especially games) may override window positioning
- **Monitor Configuration Changes**: Requires rule updates if monitor layout changes

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Include your Python version and OS version
- Provide the activity log output when reporting bugs
- Mention whether system tray features are enabled

---

**Perfect for**: Multi-monitor users, developers, traders, content creators, and anyone who wants their applications to consistently open on the correct monitor.
