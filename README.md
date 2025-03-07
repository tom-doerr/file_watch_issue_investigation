<div align="center">

# 🔍 File Watch Diagnostics

**A comprehensive toolkit for diagnosing and troubleshooting file watching issues in Linux environments**

[![Python](https://img.shields.io/badge/Python-3.6+-4B8BBE?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Watchdog](https://img.shields.io/badge/Watchdog-3.0.0-4CAF50?style=for-the-badge)](https://pypi.org/project/watchdog/)
[![PyInotify](https://img.shields.io/badge/PyInotify-0.9.6-2196F3?style=for-the-badge)](https://pypi.org/project/pyinotify/)
[![Rich](https://img.shields.io/badge/Rich-13.4.2-9C27B0?style=for-the-badge)](https://pypi.org/project/rich/)
[![PSUtil](https://img.shields.io/badge/PSUtil-5.9.5-FF5722?style=for-the-badge)](https://pypi.org/project/psutil/)

</div>

## 📋 Overview

This toolkit helps identify and resolve common problems that can cause file watching to fail or miss events in Linux environments. It provides both quick diagnostics and comprehensive analysis tools to pinpoint issues with inotify limits, filesystem compatibility, resource constraints, and more.

## 🔎 Common File Watching Issues

1. **Inotify Watch Limits**: Linux has limits on the number of inotify watches a user can have. When this limit is reached, file watching may fail silently.
2. **Filesystem Compatibility**: Some filesystems (NFS, SMBFS, etc.) have limited or no support for inotify events.
3. **Resource Constraints**: High CPU usage, memory pressure, or too many processes can cause file watching to miss events.
4. **Process-specific Issues**: Some processes may consume a large number of watches, leaving fewer for other applications.
5. **Event Coalescing**: Rapid file changes may be coalesced into fewer events, causing some changes to be missed.

## 🚀 Setup

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 🛠️ Tools

### Quick Issue Detection

The fastest way to diagnose file watching issues:

```bash
python examples/issue_detector.py [directory_to_check]
```

This will:
- Check inotify limits and current usage
- Verify filesystem compatibility
- Test event delivery
- Check for resource constraints
- Analyze watch distribution across processes

### Comprehensive Diagnostics

For a more detailed analysis:

```bash
python file_watch_diagnostics_cli.py [directory_to_monitor]
```

This will:
- Check all system limits related to file watching
- Monitor file system events in real-time
- Test file watching with different libraries
- Provide detailed logs and recommendations

### Individual Utilities

The package includes several utility modules that can be used independently:

- `system_limits.py`: Check inotify limits and current usage
- `event_monitor.py`: Monitor file system events in real-time
- `watch_test.py`: Test file watching with different libraries

## 📝 Example Usage

See the `examples` directory for example scripts:

- `basic_usage.py`: Demonstrates basic usage of the diagnostic tools
- `issue_detector.py`: Quickly identifies common file watching issues

## 🔧 Common Solutions

If issues are detected, the following solutions may help:

1. **Increase inotify limits**:
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p
   ```

2. **Use polling instead of inotify** (for incompatible filesystems):
   Configure your file watching tool to use polling instead of inotify.

3. **Reduce watch scope**:
   Watch fewer directories or use more specific patterns to reduce the number of watches needed.

4. **Restart problematic processes**:
   Identify and restart processes that are using a large number of watches.

## 📄 License

See the [LICENSE](LICENSE) file for details.
