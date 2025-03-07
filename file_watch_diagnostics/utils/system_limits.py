"""
Module for checking system limits related to file watching.
"""

import os
import subprocess
import psutil
from pathlib import Path


def get_inotify_max_user_watches():
    """Get the maximum number of inotify watches per user."""
    try:
        with open('/proc/sys/fs/inotify/max_user_watches', 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError, PermissionError) as e:
        return f"Error reading max_user_watches: {str(e)}"


def get_inotify_max_user_instances():
    """Get the maximum number of inotify instances per user."""
    try:
        with open('/proc/sys/fs/inotify/max_user_instances', 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError, PermissionError) as e:
        return f"Error reading max_user_instances: {str(e)}"


def get_inotify_max_queued_events():
    """Get the maximum number of queued events per inotify instance."""
    try:
        with open('/proc/sys/fs/inotify/max_queued_events', 'r') as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError, PermissionError) as e:
        return f"Error reading max_queued_events: {str(e)}"


def get_current_inotify_watches():
    """Get the current number of inotify watches in use."""
    try:
        # This command counts the number of inotify watches currently in use
        cmd = "find /proc/*/fd -lname '*inotify' 2>/dev/null | wc -l"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return int(result.stdout.strip())
    except Exception as e:
        return f"Error counting current watches: {str(e)}"


def get_inotify_watch_details():
    """Get detailed information about inotify watches in use."""
    try:
        # This command shows processes using inotify watches
        cmd = "find /proc/*/fd -lname '*inotify' 2>/dev/null | cut -d/ -f3 | sort | uniq -c | sort -nr"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        # Parse the output to get process details
        watch_details = []
        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue
            parts = line.strip().split()
            if len(parts) >= 2:
                count = int(parts[0])
                pid = int(parts[1])
                try:
                    process = psutil.Process(pid)
                    watch_details.append({
                        'pid': pid,
                        'name': process.name(),
                        'cmdline': ' '.join(process.cmdline()),
                        'watch_count': count
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    watch_details.append({
                        'pid': pid,
                        'name': 'Unknown (process no longer exists or access denied)',
                        'cmdline': 'Unknown',
                        'watch_count': count
                    })
        return watch_details
    except (subprocess.SubprocessError, ValueError) as e:
        return f"Error getting watch details: {str(e)}"


def get_filesystem_info(path):
    """Get filesystem information for the specified path."""
    path = Path(path).resolve()
    try:
        stat = os.statvfs(path)
        return {
            'path': str(path),
            'filesystem_type': get_filesystem_type(path),
            'total_space_gb': stat.f_blocks * stat.f_frsize / (1024**3),
            'free_space_gb': stat.f_bfree * stat.f_frsize / (1024**3),
            'inodes_total': stat.f_files,
            'inodes_free': stat.f_ffree,
            'max_filename_length': stat.f_namemax
        }
    except OSError as e:
        return f"Error getting filesystem info for {path}: {str(e)}"


def get_filesystem_type(path):
    """Get the filesystem type for the specified path."""
    try:
        cmd = f"df -T {path} | tail -1 | awk '{{print $2}}'"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.SubprocessError as e:
        return f"Error determining filesystem type: {str(e)}"


def check_system_limits():
    """Check all system limits related to file watching."""
    return {
        'max_user_watches': get_inotify_max_user_watches(),
        'max_user_instances': get_inotify_max_user_instances(),
        'max_queued_events': get_inotify_max_queued_events(),
        'current_watches': get_current_inotify_watches(),
        'watch_details': get_inotify_watch_details()
    }


if __name__ == "__main__":
    import json
    print(json.dumps(check_system_limits(), indent=2, default=str))
