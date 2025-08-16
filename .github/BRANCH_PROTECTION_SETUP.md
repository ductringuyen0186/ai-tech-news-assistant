# Branch Protection Setup Guide

## Quick Setup Steps:

1. **Go to Repository Settings → Branches**:
   https://github.com/ductringuyen0186/ai-tech-news-assistant/settings/branches

2. **Click "Add rule" for the `main` branch**

3. **Required Settings**:
   ```
   Branch name pattern: main
   
   ✅ Require a pull request before merging
   ✅ Require approvals: 1
   ✅ Dismiss stale reviews when new commits are pushed
   
   ✅ Require status checks to pass before merging
   ✅ Require branches to be up to date before merging
   
   Required status checks:
   - ✅ code-quality
   - ✅ build-and-test
   - ⚠️ security-scan (optional - only runs on main)
   
   ✅ Require conversation resolution before merging
   ✅ Include administrators (applies rules to repo admins too)
   ```

## What This Achieves:

- ✅ **No direct pushes to main** - Must use PR
- ✅ **CI must pass** - All tests/builds must succeed  
- ✅ **Code review required** - At least 1 approval needed
- ✅ **Up-to-date branches** - Must rebase/merge latest main
- ✅ **No merge conflicts** - Conversations must be resolved

## Current CI Jobs That Will Be Required:

1. **code-quality** - Python formatting, JS/TS linting
2. **build-and-test** - Backend tests + Frontend builds
3. **security-scan** - Vulnerability scanning (main branch only)

After setup, your PR #39 will show "⚠️ Required checks" and prevent merging until CI passes!
