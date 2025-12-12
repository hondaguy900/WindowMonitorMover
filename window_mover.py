import tkinter as tk
from tkinter import ttk, messagebox
import win32gui
import win32con
import win32process
import psutil
import threading
import time
import json
import os
import ctypes
from ctypes import wintypes

# Try to import system tray libraries
TRAY_AVAILABLE = False
pystray = None
Image = None
ImageDraw = None

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
    print("System tray support enabled")
except ImportError as e:
    print(f"Warning: pystray and/or PIL not installed. System tray will not be available.")
    print(f"Error: {e}")
    print("Install with: pip install pystray pillow")

print(f"TRAY_AVAILABLE is set to: {TRAY_AVAILABLE}")

class AddRuleDialog:
    def __init__(self, parent, callback, existing_rule=None, target_monitor=None):
        self.window = tk.Toplevel(parent)
        self.window.title("Add Rule - Drag to Target Monitor" if not existing_rule else "Edit Rule - Drag to Target Monitor")
        
        self.callback = callback
        self.monitor_num = None
        self.existing_rule = existing_rule
        
        # Position window on target monitor if provided
        if target_monitor:
            # Calculate center of target monitor
            mon_width = target_monitor['right'] - target_monitor['left']
            mon_height = target_monitor['bottom'] - target_monitor['top']
            win_width = 500
            win_height = 550
            
            x = target_monitor['left'] + (mon_width - win_width) // 2
            y = target_monitor['top'] + (mon_height - win_height) // 2
            
            self.window.geometry(f"{win_width}x{win_height}+{x}+{y}")
        else:
            self.window.geometry("500x550")
        
        self.window.configure(bg='#FFD700')
        
        # Make window stay on top
        self.window.attributes('-topmost', True)
        
        # Big instructions
        instructions = tk.Label(self.window, 
                              text="1. Select process from list or type name\n"
                                   "2. DRAG THIS WINDOW to your target monitor\n"
                                   "3. Choose window size behavior\n"
                                   "4. Click Save\n"
                                   "5. Click Start Monitoring when ready to activate all rules",
                              font=("Arial", 11, "bold"),
                              bg='#FFD700',
                              fg='#000000',
                              justify=tk.LEFT)
        instructions.pack(pady=12, padx=20, anchor=tk.W)
        
        # Process selection
        select_frame = tk.Frame(self.window, bg='#FFD700')
        select_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(select_frame, text="Select Running Process:", 
                font=("Arial", 10, "bold"), bg='#FFD700').pack(anchor=tk.W, pady=5)
        
        # Listbox with scrollbar for processes
        list_frame = tk.Frame(select_frame, bg='#FFD700')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.process_listbox = tk.Listbox(list_frame, 
                                         yscrollcommand=scrollbar.set,
                                         font=("Consolas", 9),
                                         height=6)
        self.process_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.process_listbox.yview)
        
        # Populate with running processes
        self.populate_processes()
        
        # Manual entry option
        tk.Label(select_frame, text="Or type manually:", 
                font=("Arial", 10, "bold"), bg='#FFD700').pack(anchor=tk.W, pady=(10, 5))
        
        self.process_entry = tk.Entry(select_frame, font=("Arial", 10))
        self.process_entry.pack(fill=tk.X)
        
        # Pre-fill if editing
        if existing_rule:
            self.process_entry.insert(0, existing_rule['process'])
        
        # Bind listbox selection to update entry
        self.process_listbox.bind('<<ListboxSelect>>', self.on_process_select)
        
        # Window size options
        size_frame = tk.Frame(self.window, bg='#FFD700')
        size_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(size_frame, text="Window Size:", 
                font=("Arial", 10, "bold"), bg='#FFD700').pack(anchor=tk.W, pady=5)
        
        self.window_size = tk.StringVar(value=existing_rule.get('size', 'normal') if existing_rule else 'normal')
        
        size_options = tk.Frame(size_frame, bg='#FFD700')
        size_options.pack(fill=tk.X)
        
        tk.Radiobutton(size_options, text="Keep Current Size (default)", 
                      variable=self.window_size, value="normal",
                      bg='#FFD700', font=("Arial", 9),
                      selectcolor='#FFD700').pack(anchor=tk.W)
        
        tk.Radiobutton(size_options, text="Maximize After Moving", 
                      variable=self.window_size, value="maximized",
                      bg='#FFD700', font=("Arial", 9),
                      selectcolor='#FFD700').pack(anchor=tk.W)
        
        tk.Radiobutton(size_options, text="Minimize After Moving", 
                      variable=self.window_size, value="minimized",
                      bg='#FFD700', font=("Arial", 9),
                      selectcolor='#FFD700').pack(anchor=tk.W)
        
        # Buttons
        btn_frame = tk.Frame(self.window, bg='#FFD700')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save Rule", 
                 command=self.save_rule,
                 font=("Arial", 11, "bold"),
                 bg='#4CAF50',
                 fg='white',
                 padx=20,
                 pady=8).pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="✖ Cancel", 
                 command=self.window.destroy,
                 font=("Arial", 11),
                 bg='#f44336',
                 fg='white',
                 padx=20,
                 pady=8).pack(side=tk.LEFT, padx=10)
    
    def populate_processes(self):
        """Get all running processes with windows"""
        processes = set()
        
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    parent = win32gui.GetParent(hwnd)
                    title = win32gui.GetWindowText(hwnd)
                    
                    if parent == 0 and title:  # Top-level windows with titles
                        proc_name = proc.name().replace('.exe', '')
                        processes.add(proc_name)
                except:
                    pass
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        
        # Sort alphabetically (case-insensitive) and add to listbox
        for proc in sorted(processes, key=str.lower):
            self.process_listbox.insert(tk.END, proc)
    
    def on_process_select(self, event):
        """When user selects from listbox, update entry"""
        selection = self.process_listbox.curselection()
        if selection:
            process = self.process_listbox.get(selection[0])
            self.process_entry.delete(0, tk.END)
            self.process_entry.insert(0, process)
    
    def save_rule(self):
        process_name = self.process_entry.get().strip()
        if not process_name:
            messagebox.showwarning("Error", "Enter a process name")
            return
        
        # Remove .exe if present
        process_name = process_name.replace('.exe', '').replace('.EXE', '')
        
        # Get which monitor this window is on
        monitor_num = self.get_monitor_number()
        
        # Get window size preference
        window_size = self.window_size.get()
        
        if monitor_num:
            self.callback(process_name, monitor_num, window_size)
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Could not detect monitor")
    
    def get_monitor_number(self):
        """Detect which monitor this window is on"""
        # Get window position
        x = self.window.winfo_x()
        y = self.window.winfo_y()
        
        # Get all monitors
        monitors = []
        user32 = ctypes.windll.user32
        
        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD)
            ]
        
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_double
        )
        
        def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            
            if user32.GetMonitorInfoA(hMonitor, ctypes.byref(info)):
                rect = info.rcMonitor
                monitors.append({
                    'left': rect.left,
                    'top': rect.top,
                    'right': rect.right,
                    'bottom': rect.bottom,
                    'is_primary': bool(info.dwFlags & 1)
                })
            return 1
        
        user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
        
        # Sort monitors: primary first, then by position
        monitors = sorted(monitors, key=lambda m: (
            0 if m['is_primary'] else 1,
            m['left'],
            m['top']
        ))
        
        # Find which monitor contains this point
        for i, mon in enumerate(monitors, 1):
            if (x >= mon['left'] and x < mon['right'] and 
                y >= mon['top'] and y < mon['bottom']):
                return {'number': i, 'info': mon}
        
        return None

class WindowMoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Window Monitor Mover")
        self.root.geometry("700x700")
        
        self.monitoring = False
        self.rules = []
        self.moved_windows = set()
        self.config_file = "window_mover_config.json"
        self.tray_icon = None
        self.tray_available = TRAY_AVAILABLE
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.setup_ui()
        self.load_config()
        
        # Create tray icon if available
        if self.tray_available:
            self.create_tray_icon()
            # Set initial taskbar icon to red (stopped state)
            self.update_taskbar_icon(False)
        
        # Auto-start monitoring if rules exist
        if self.rules:
            self.log("Auto-starting monitoring (rules found)")
            self.root.after(500, self.start_monitoring)  # Small delay to ensure UI is ready
        
    def setup_ui(self):
        # Header with Exit button
        header = ttk.Frame(self.root, padding="10")
        header.pack(fill=tk.X)
        
        # Title in center
        title_frame = ttk.Frame(header)
        title_frame.pack(expand=True)
        
        ttk.Label(title_frame, text="Window Monitor Mover", 
                 font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(title_frame, text="Automatically move application windows to specified monitors", 
                 font=("Segoe UI", 9)).pack()
        
        # Exit button in top-right
        exit_btn = ttk.Button(header, text="✖ Exit", command=self.quit_app, width=8)
        exit_btn.place(relx=1.0, rely=0, anchor='ne')
        
        # Rules List
        list_frame = ttk.LabelFrame(self.root, text="Active Rules", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.rules_listbox = tk.Listbox(list_container, 
                                        yscrollcommand=scrollbar.set,
                                        font=("Consolas", 10))
        self.rules_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.rules_listbox.yview)
        
        # Rule management buttons
        btn_row = ttk.Frame(list_frame)
        btn_row.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_row, text="➕ Add New Rule", 
                  command=self.show_add_rule_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="✏️ Edit Selected", 
                  command=self.edit_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_row, text="🗑 Remove Selected", 
                  command=self.remove_rule).pack(side=tk.LEFT, padx=5)
        
        # Note at bottom of Active Rules section
        note_label = ttk.Label(list_frame, 
                              text="Note: Monitor numbers are assigned by the app and may differ from Windows Display Settings", 
                              font=("Segoe UI", 8), 
                              foreground="gray")
        note_label.pack(pady=(5, 0))
        
        # Control Panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)
        
        self.start_btn = ttk.Button(control_frame, text="▶ Start Monitoring",
                                    command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⬛ Stop Monitoring",
                                   command=self.stop_monitoring,
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🔄 Restart Monitoring",
                  command=self.restart_monitoring).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Clear Log",
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(control_frame, text="⚫ Not Monitoring",
                                     font=("Segoe UI", 10))
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD,
                               yscrollcommand=log_scroll.set,
                               font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def show_add_rule_dialog(self):
        """Show the drag-to-target dialog"""
        AddRuleDialog(self.root, self.add_rule_callback)
    
    def edit_rule(self):
        """Edit selected rule"""
        sel = self.rules_listbox.curselection()
        if not sel:
            messagebox.showwarning("Error", "Select a rule to edit")
            return
        
        idx = sel[0]
        rule = self.rules[idx]
        
        # Show dialog with existing rule, positioned on rule's target monitor
        AddRuleDialog(self.root, self.add_rule_callback, rule, rule['monitor'])
    
    def add_rule_callback(self, process_name, monitor_info, window_size):
        """Called when user saves a rule from the dialog"""
        monitor_num = monitor_info['number']
        monitor_pos = monitor_info['info']
        
        rule = {
            "process": process_name,
            "monitor": monitor_pos,  # Store the actual position/bounds
            "size": window_size      # Store window size preference
        }
        
        # Check for duplicates and update
        existing_idx = None
        for i, existing_rule in enumerate(self.rules):
            if existing_rule['process'].lower() == process_name.lower():
                existing_idx = i
                break
        
        # Create display text
        size_icon = ""
        if window_size == "maximized":
            size_icon = " [MAX]"
        elif window_size == "minimized":
            size_icon = " [MIN]"
        
        display_text = f"{process_name:25} → Monitor {monitor_num}{size_icon}"
        
        if existing_idx is not None:
            # Update existing rule
            self.rules[existing_idx] = rule
            self.rules_listbox.delete(existing_idx)
            self.rules_listbox.insert(existing_idx, display_text)
            self.log(f"Updated: {process_name} → Monitor {monitor_num} ({window_size})")
        else:
            # Add new rule
            self.rules.append(rule)
            self.rules_listbox.insert(tk.END, display_text)
            self.log(f"Added: {process_name} → Monitor {monitor_num} ({window_size})")
        
        self.save_config()
    
    def restart_monitoring(self):
        """Restart monitoring (useful after changing rules)"""
        if self.monitoring:
            self.stop_monitoring()
            time.sleep(0.5)
        self.start_monitoring()
            
    def remove_rule(self):
        sel = self.rules_listbox.curselection()
        if not sel:
            messagebox.showwarning("Error", "Select a rule to remove")
            return
        
        idx = sel[0]
        rule = self.rules[idx]
        self.rules.pop(idx)
        self.rules_listbox.delete(idx)
        self.save_config()
        self.log(f"Removed: {rule['process']}")
        
    def save_config(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.rules, f, indent=2)
        except Exception as e:
            self.log(f"Save error: {e}")
            
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.rules = json.load(f)
                
                for rule in self.rules:
                    # Determine monitor number from position
                    mon_num = self.get_monitor_number_from_bounds(rule['monitor'])
                    
                    # Get window size
                    size = rule.get('size', 'normal')
                    size_icon = ""
                    if size == "maximized":
                        size_icon = " [MAX]"
                    elif size == "minimized":
                        size_icon = " [MIN]"
                    
                    self.rules_listbox.insert(tk.END, 
                        f"{rule['process']:25} → Monitor {mon_num}{size_icon}")
                
                self.log(f"Loaded {len(self.rules)} rules")
            except Exception as e:
                self.log(f"Load error: {e}")
    
    def get_monitor_number_from_bounds(self, target_monitor):
        """Get monitor number from monitor bounds"""
        monitors = self.get_all_monitors()
        
        for i, mon in enumerate(monitors, 1):
            if (mon['left'] == target_monitor['left'] and 
                mon['top'] == target_monitor['top']):
                return i
        
        return "?"
    
    def get_all_monitors(self):
        """Get all monitors"""
        monitors = []
        user32 = ctypes.windll.user32
        
        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD)
            ]
        
        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(wintypes.RECT),
            ctypes.c_double
        )
        
        def callback(hMonitor, hdcMonitor, lprcMonitor, dwData):
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            
            if user32.GetMonitorInfoA(hMonitor, ctypes.byref(info)):
                rect = info.rcMonitor
                monitors.append({
                    'left': rect.left,
                    'top': rect.top,
                    'right': rect.right,
                    'bottom': rect.bottom,
                    'is_primary': bool(info.dwFlags & 1)
                })
            return 1
        
        user32.EnumDisplayMonitors(None, None, MonitorEnumProc(callback), 0)
        
        # Sort: primary first, then by position
        return sorted(monitors, key=lambda m: (
            0 if m['is_primary'] else 1,
            m['left'],
            m['top']
        ))
                
    def find_windows(self, process_name):
        """Find all windows for a process"""
        windows = []
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    proc = psutil.Process(pid)
                    proc_name = proc.name().replace('.exe', '').lower()
                    
                    if proc_name == process_name.lower():
                        parent = win32gui.GetParent(hwnd)
                        if parent == 0:
                            title = win32gui.GetWindowText(hwnd)
                            windows.append({
                                'hwnd': hwnd,
                                'title': title or "(No Title)"
                            })
                except:
                    pass
            return True
        
        win32gui.EnumWindows(callback, None)
        return windows
        
    def move_window(self, hwnd, target_monitor, window_size="normal"):
        """Move window to target monitor and apply size preference"""
        
        try:
            # Get current placement
            placement = win32gui.GetWindowPlacement(hwnd)
            current_state = placement[1]
            was_maximized = (current_state == win32con.SW_SHOWMAXIMIZED)
            
            # Restore maximized windows FIRST so we can get their true position
            if was_maximized:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.15)
            
            # NOW get the actual window position and size
            rect = win32gui.GetWindowRect(hwnd)
            current_x = rect[0]
            current_y = rect[1]
            w = rect[2] - rect[0]
            h = rect[3] - rect[1]
            
            # Check if already on target monitor
            already_on_target = (current_x >= target_monitor['left'] and 
                                current_x < target_monitor['right'] and
                                current_y >= target_monitor['top'] and 
                                current_y < target_monitor['bottom'])
            
            # Check if already in desired state (after restore, so was_maximized tells us original state)
            desired_state_matches = False
            if window_size == "maximized" and was_maximized and already_on_target:
                desired_state_matches = True
            elif window_size == "minimized" and current_state == win32con.SW_SHOWMINIMIZED:
                desired_state_matches = True
            elif window_size == "normal" and not was_maximized and current_state != win32con.SW_SHOWMINIMIZED:
                desired_state_matches = True
            
            # Only skip if BOTH on target monitor AND in desired state
            if already_on_target and desired_state_matches:
                # Re-maximize if it was maximized and should stay maximized
                if was_maximized and window_size == "maximized":
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                return True
            
            # Target position
            x = target_monitor['left'] + 50
            y = target_monitor['top'] + 50
            
            # Move window to target monitor
            win32gui.SetWindowPos(hwnd, 0, x, y, w, h,
                                 win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW)
            time.sleep(0.15)
            
            # Apply size preference AFTER moving
            if window_size == "maximized":
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                time.sleep(0.1)
                return True  # Don't verify position for maximized windows
            elif window_size == "minimized":
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                time.sleep(0.1)
                return True  # Don't verify position for minimized windows
            
            # Verify for normal windows only
            new_rect = win32gui.GetWindowRect(hwnd)
            nx = new_rect[0]
            ny = new_rect[1]
            
            success = (nx >= target_monitor['left'] and nx < target_monitor['right'] and
                      ny >= target_monitor['top'] and ny < target_monitor['bottom'])
                
            return success
            
        except Exception as e:
            self.log(f"  Move error: {e}")
            return False
            
    def monitor_thread(self):
        """Background monitoring thread"""
        self.log("Monitoring started")
        self.moved_windows.clear()
        
        while self.monitoring:
            try:
                for rule in self.rules:
                    proc = rule['process']
                    target_mon = rule['monitor']
                    window_size = rule.get('size', 'normal')  # Default to normal for old configs
                    
                    windows = self.find_windows(proc)
                    
                    for window in windows:
                        hwnd = window['hwnd']
                        
                        if hwnd not in self.moved_windows:
                            title = window['title']
                            self.log(f"Found: {proc} - {title[:40]}")
                            
                            if self.move_window(hwnd, target_mon, window_size):
                                size_text = f" ({window_size})" if window_size != "normal" else ""
                                self.log(f"  ✓ Moved to target monitor{size_text}")
                                self.moved_windows.add(hwnd)
                            else:
                                self.log(f"  ✗ Failed to move")
                
                # Clean up closed windows
                valid = set()
                for rule in self.rules:
                    wins = self.find_windows(rule['process'])
                    valid.update(w['hwnd'] for w in wins)
                self.moved_windows &= valid
                
            except Exception as e:
                self.log(f"Error: {e}")
                
            time.sleep(0.5)
            
        self.log("Monitoring stopped")
        
    def start_monitoring(self):
        if not self.rules:
            messagebox.showwarning("Error", "Add at least one rule first")
            return
        
        self.monitoring = True
        thread = threading.Thread(target=self.monitor_thread, daemon=True)
        thread.start()
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="🟢 Monitoring Active", foreground="green")
        
        # Update both tray and taskbar icons to green
        self.update_tray_icon(True)
        self.update_taskbar_icon(True)
        
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⚫ Not Monitoring", foreground="black")
        
        # Update both tray and taskbar icons to red
        self.update_tray_icon(False)
        self.update_taskbar_icon(False)
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not self.tray_available:
            return
        
        # Create icons for different states
        def create_icon_image(color='#f44336'):
            # Create a 64x64 image with a colored circle
            img = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill=color, outline='#2E7D32' if color == '#4CAF50' else '#C62828')
            return img
        
        # Start with red icon (stopped state)
        icon_image = create_icon_image('#f44336')
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show Window", self.show_window, default=True),  # default=True makes it double-click action
            pystray.MenuItem("Start Monitoring", self.start_monitoring_from_tray, 
                           visible=lambda item: not self.monitoring),
            pystray.MenuItem("Stop Monitoring", self.stop_monitoring_from_tray,
                           visible=lambda item: self.monitoring),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("WindowMover", icon_image, 
                                      "Window Monitor Mover", menu)
        
        # Run tray icon in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def update_tray_icon(self, monitoring):
        """Update tray icon color based on monitoring state"""
        if not self.tray_available or not self.tray_icon:
            return
        
        def create_icon_image(color):
            img = Image.new('RGB', (64, 64), color='white')
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill=color, outline='#2E7D32' if color == '#4CAF50' else '#C62828')
            return img
        
        # Green = monitoring active, Red = stopped
        color = '#4CAF50' if monitoring else '#f44336'
        self.tray_icon.icon = create_icon_image(color)
    
    def update_taskbar_icon(self, monitoring):
        """Update taskbar icon color based on monitoring state"""
        if not self.tray_available:
            return
        
        try:
            # Create icon for taskbar
            def create_taskbar_icon(color):
                img = Image.new('RGB', (32, 32), color='white')
                draw = ImageDraw.Draw(img)
                draw.ellipse([4, 4, 28, 28], fill=color, outline='#2E7D32' if color == '#4CAF50' else '#C62828')
                return img
            
            # Green = monitoring active, Red = stopped
            color = '#4CAF50' if monitoring else '#f44336'
            icon_img = create_taskbar_icon(color)
            
            # Convert PIL image to PhotoImage for tkinter
            import io
            with io.BytesIO() as output:
                icon_img.save(output, format="PNG")
                icon_data = output.getvalue()
            
            # Save to temp file and set as icon
            temp_icon_path = "temp_icon.ico"
            icon_img.save(temp_icon_path, format="ICO")
            self.root.iconbitmap(temp_icon_path)
            
        except Exception as e:
            # If setting icon fails, just continue without it
            pass
    
    def on_closing(self):
        """Handle window close - minimize to tray instead"""
        if self.tray_available and self.tray_icon:
            self.root.withdraw()  # Hide window
            self.tray_icon.notify("Window Monitor Mover is running in the system tray", 
                                 "Window Monitor Mover")
        else:
            # If no tray available, just minimize normally
            self.root.iconify()
    
    def show_window(self):
        """Show window from tray"""
        self.root.deiconify()  # Show window
        self.root.lift()  # Bring to front
        self.root.focus_force()
    
    def start_monitoring_from_tray(self):
        """Start monitoring from tray menu"""
        self.root.after(0, self.start_monitoring)
    
    def stop_monitoring_from_tray(self):
        """Stop monitoring from tray menu"""
        self.root.after(0, self.stop_monitoring)
    
    def quit_app(self):
        """Completely quit the application"""
        self.monitoring = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowMoverApp(root)
    root.mainloop()