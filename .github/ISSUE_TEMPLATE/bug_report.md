---
name: Bug Report
about: Create a report to help us improve PondMonitor
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
**Describe the bug**
A clear and concise description of what the bug is.

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Actual Behavior**
A clear and concise description of what actually happened.

## Reproduction Steps
**Steps to reproduce the behavior:**
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

**Minimal code example** (if applicable):
```python
# Your code here
```

## Environment Information
**PondMonitor Version:**
- Version/Tag: [e.g., v2.5.0, latest]
- Branch: [e.g., main, refactor/milestone1-foundation]
- Commit SHA: [if known]

**System Environment:**
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS Monterey]
- Python version: [e.g., 3.11.2]
- Docker version: [e.g., 24.0.2]
- Browser: [e.g., Chrome 114, Firefox 115] (if web-related)

**Hardware Setup:**
- [ ] Testing mode (simulated data)
- [ ] Production mode with real hardware
- LoRa device: [if applicable]
- USB/Serial device: [if applicable]

## Error Details
**Error Messages:**
```
Paste any error messages here
```

**Log Output:**
```
# From docker-compose logs or application logs
Paste relevant log entries here
```

**Screenshots:**
If applicable, add screenshots to help explain your problem.

## Additional Context
**Configuration:**
- [ ] Using default configuration
- [ ] Custom configuration (please describe)

**Database:**
- Database type: [TimescaleDB/PostgreSQL]
- Database version: [if known]
- Data volume: [approximate number of records]

**Services Status:**
```bash
# Output of: curl http://localhost:5000/api/diagnostics
```

**Additional context:**
Add any other context about the problem here.

## Possible Solution
If you have suggestions on how to fix the issue, please describe them here.

## Checklist
- [ ] I have searched existing issues to make sure this is not a duplicate
- [ ] I have included all relevant information above
- [ ] I can reproduce this issue consistently
- [ ] I have checked the [Troubleshooting Guide](../docs/TROUBLESHOOTING.md)