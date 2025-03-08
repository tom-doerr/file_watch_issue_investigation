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

## 📁 Project Structure

```
file_watch_diagnostics/
├── cli/                  # Command-line interfaces
│   ├── diagnostics.py    # Full diagnostics CLI
│   └── quick_check.py    # Quick check CLI
├── utils/                # Utility modules
│   ├── event_monitor.py  # File system event monitoring
│   ├── logging_utils.py  # Logging utilities
│   ├── system_limits.py  # System limits checking
│   └── watch_test.py     # File watching library tests
└── diagnostics.py        # Core diagnostics functionality
```

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

### Comprehensive Diagnostics

For a more detailed analysis:

```bash
python -m file_watch_diagnostics.cli.diagnostics [directory] --testing-mode
```

This will:
- Check all system limits related to file watching
- Monitor file system events in real-time
- Test file watching with different libraries
- Provide detailed logs and recommendations

### Quick Check

For a faster, targeted analysis:

```bash
python -m file_watch_diagnostics.cli.quick_check --directory /path/to/directory --testing
```

This performs a subset of the full diagnostics, focusing on the most common issues.

### Individual Utilities

The package includes several utility modules that can be used independently:

- `system_limits.py`: Check inotify limits and current usage
- `event_monitor.py`: Monitor file system events in real-time
- `watch_test.py`: Test file watching with different libraries

## 📝 Example Usage

See the `examples` directory for example scripts:

- `basic_usage.py`: Demonstrates basic usage of the diagnostic tools
- `issue_detector.py`: Quickly identifies common file watching issues

## 🧪 Testing

The package includes both unit tests and integration tests to ensure functionality.

### Running Unit Tests

```bash
python -m pytest /path/to/file_watch_issue_investigation/tests/ -v
```

### Running Integration Tests

```bash
python -m pytest /path/to/file_watch_issue_investigation/tests/integration/ -v
```

### Running Tests with Coverage

```bash
python -m pytest /path/to/file_watch_issue_investigation/tests/ --cov=file_watch_diagnostics
```

### Test Configuration

The project uses pytest.ini for test configuration:
- Default test discovery in the `tests` directory
- Integration tests are marked with the `integration` marker
- Warnings from third-party libraries are filtered

### Test Coverage

Current test coverage is at 83%, with the following breakdown:
- CLI modules: 93-94%
- Core diagnostics: 81%
- Event monitoring: 81%
- System limits: 78%
- Watch testing: 83%
- Logging utilities: 72%

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

## 🚧 Development Status

This project is actively maintained and tested. Current focus areas include:

- Improving test coverage, especially for error handling paths
- Optimizing event monitoring performance
- Enhancing the CLI interfaces for better user experience
- Adding more comprehensive documentation

## 🔮 Future Improvements

Planned improvements include:

- Adding type hints for better code readability and static type checking
- Creating a simplified API for common diagnostic tasks
- Supporting more file watching libraries and frameworks
- Providing more detailed recommendations for fixing detected issues
- Adding visualization tools for monitoring file watching performance
