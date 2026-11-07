#!/usr/bin/env python3
"""
notify_macos.py — Нативный мост уведомлений macOS Notification Center (без звука).
Принципы: Think in Code (Правило №16), Silent Native Alerts.
"""

import sys
import subprocess

def send_notification(title, message, subtitle=""):
    apple_script = f'display notification "{message}" with title "{title}"'
    if subtitle:
        apple_script += f' subtitle "{subtitle}"'
    
    try:
        subprocess.run(["osascript", "-e", apple_script], check=True, capture_output=True)
        return True
    except Exception as e:
        return False

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 notify_macos.py <title> <message> [subtitle]")
        sys.exit(1)
        
    title = sys.argv[1]
    message = sys.argv[2]
    subtitle = sys.argv[3] if len(sys.argv) > 3 else ""
    success = send_notification(title, message, subtitle)
    if success:
        print(f"🔔 [macOS Notification] {title}: {message}")
    else:
        print(f"⚠️ [Notification Error] Не удалось отправить уведомление.")

if __name__ == "__main__":
    main()
