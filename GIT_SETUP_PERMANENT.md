# Git Configuration - Permanent Fix for Tag Issues

**Issue**: `! [rejected] v1.0.0 -> v1.0.0 (would clobber existing tag)`

**Root Cause**: Local tags conflict with remote tags when they point to different commits.

---

## ✅ Permanent Solution Applied

### **1. Automatic Tag Pruning**
```bash
git config --local fetch.pruneTags true
```
This automatically removes local tags that don't exist on remote during fetch.

### **2. Custom Sync Alias**
```bash
git config --local alias.sync '!git fetch origin --tags --force && git pull origin $(git branch --show-current)'
```

---

## 🚀 How to Use (Going Forward)

### **Option 1: Use the Sync Alias** (Recommended)
```bash
git sync
```
This will:
1. Force-fetch all tags from remote
2. Pull the current branch
3. Never show tag conflicts

### **Option 2: Manual Pull with Force**
```bash
git fetch origin --tags --force && git pull origin main
```

### **Option 3: Standard Pull (Now Fixed)**
```bash
git pull --tags origin main
```
Should work without errors now due to `fetch.pruneTags = true`.

---

## 🔧 What Was Configured

### **Repository Settings**
```bash
# View all custom configs
git config --local --list
```

**Key settings**:
- `fetch.pruneTags = true` - Auto-remove stale local tags
- `tag.forcesignannotated = false` - Don't require signed tags
- `alias.sync = ...` - Custom sync command

---

## 🛠️ Troubleshooting

### **If Tag Conflicts Still Appear**

**Quick fix**:
```bash
git fetch origin --tags --force
```

**Nuclear option** (deletes ALL local tags and re-downloads):
```bash
git tag -l | xargs git tag -d  # Delete all local tags
git fetch origin --tags          # Re-download from remote
```

### **Check Tag Differences**
```bash
# See local tags
git tag -l

# See remote tags
git ls-remote --tags origin

# Compare specific tag
git show v1.0.0
git show origin/v1.0.0
```

---

## 📋 Common Git Workflows (Now Simplified)

### **Daily Work**
```bash
# Start of day
git sync

# Make changes
git add .
git commit -m "Your message"

# Push
git push origin main
```

### **Working with Tags**
```bash
# Create new tag
git tag -a v1.0.5 -m "Release v1.0.5"

# Push tag
git push origin v1.0.5

# Sync all tags
git sync  # Will update any changed tags automatically
```

### **Branch Work**
```bash
# Create branch
git checkout -b feature-branch

# Sync while on branch
git sync  # Works on any branch!

# Push branch
git push origin feature-branch
```

---

## ⚠️ Important Notes

### **Why This Happened**

Tags were likely created locally and then recreated on GitHub (e.g., during Zenodo releases), causing the commit hashes to differ. The `--force` flag on fetch resolves this by trusting the remote.

### **Best Practices**

1. **Always use `git sync`** instead of `git pull --tags`
2. **Don't manually edit tags** - delete and recreate instead
3. **Push tags immediately** after creating: `git push origin v1.0.x`
4. **Use annotated tags** for releases: `git tag -a v1.0.x -m "Message"`

### **Safe Operations**

These commands will NEVER lose your work:
- `git fetch origin --tags --force` ✅ Safe (only updates tags)
- `git sync` ✅ Safe (fetches then pulls)
- `git pull origin main` ✅ Safe (standard pull)

These are destructive (use carefully):
- `git tag -d v1.0.0` ⚠️ Deletes local tag
- `git push --delete origin v1.0.0` ⚠️ Deletes remote tag
- `git tag -f v1.0.0` ⚠️ Force moves tag (confusing for others)

---

## 🎯 Quick Reference Card

| Task | Command |
|------|---------|
| **Daily sync** | `git sync` |
| **Pull with tags** | `git pull --tags origin main` |
| **Force update tags** | `git fetch origin --tags --force` |
| **Check config** | `git config --local --list` |
| **List local tags** | `git tag -l` |
| **List remote tags** | `git ls-remote --tags origin` |
| **Delete local tag** | `git tag -d v1.0.0` |
| **Create tag** | `git tag -a v1.0.0 -m "Message"` |
| **Push tag** | `git push origin v1.0.0` |

---

## 🔄 Reset Configuration (If Needed)

If you ever want to undo these changes:

```bash
# Remove custom alias
git config --local --unset alias.sync

# Remove tag pruning
git config --local --unset fetch.pruneTags

# View remaining config
git config --local --list
```

---

## ✅ Verification

To verify everything is working:

```bash
# Should show no errors
git pull --tags origin main

# Should show custom alias
git config --local alias.sync

# Should show "true"
git config --local fetch.pruneTags
```

---

**Configured**: October 22, 2025
**Repository**: EleutherIA (Ancient Free Will Database)
**Status**: ✅ Permanent fix applied - no more tag conflicts!

---

## 💡 Pro Tip

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) for ALL repositories:

```bash
# Git alias for all repos
alias gitsync='git fetch origin --tags --force && git pull origin $(git branch --show-current)'
```

Then you can use `gitsync` in any repository!
