# Security Remediation - API Key Exposure

**Date:** 2025-10-18
**Status:** URGENT - Action Required
**Severity:** HIGH

## Issue Summary

A Gemini API key was accidentally committed to the public git repository in `setup_embeddings.sh` (line 17, commit fe5a4d5).

## Actions Taken ✅

1. **Removed hardcoded API key** from `setup_embeddings.sh`
2. **Updated script** to use environment variables from `.env` file
3. **Enhanced .gitignore** to include `.claude/settings.local.json`

## Actions Required 🚨

### CRITICAL: Revoke Exposed API Keys

Since this repository is public, you MUST revoke the exposed API key(s) immediately:

1. Go to [Google Cloud Console - API Keys](https://console.cloud.google.com/apis/credentials)
2. Find and **DELETE** or **REVOKE** these keys:
   - `AIzaSyDB_n4uxyXFIijMeN0imzZ3cbNjR-w3hrw` (exposed in git history)
   - `AIzaSyBS6WTXFT3Z3xjhcE9_0McvpIRcHDsxD_M` (shared in this conversation - assume compromised)
3. **Generate a NEW API key**
4. Update your `.env` file with the new key:
   ```bash
   GEMINI_API_KEY=your_new_key_here
   ```

### Remove API Key from Git History

The old API key is in git history (commit fe5a4d5). You have two options:

#### Option 1: Using git-filter-repo (Recommended)

```bash
# Install git-filter-repo if needed
pip install git-filter-repo

# Create a backup first!
cd .. && cp -r "Ancient Free Will Database" "Ancient Free Will Database.backup"
cd "Ancient Free Will Database"

# Replace the API key in history with a placeholder
git filter-repo --replace-text <(echo "AIzaSyDB_n4uxyXFIijMeN0imzZ3cbNjR-w3hrw==>***REMOVED_API_KEY***")

# Force push to update remote repository
git push origin --force --all
git push origin --force --tags
```

#### Option 2: Using BFG Repo-Cleaner

```bash
# Download BFG: https://rtyley.github.io/bfg-repo-cleaner/

# Create a backup first!
cd .. && cp -r "Ancient Free Will Database" "Ancient Free Will Database.backup"

# Clone a mirror
git clone --mirror https://github.com/yourusername/yourrepo.git

# Run BFG
java -jar bfg.jar --replace-text passwords.txt yourrepo.git

# Clean up and push
cd yourrepo.git
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git push --force
```

#### Option 3: Nuclear Option - Squash History (If acceptable)

If you don't need to preserve commit history:

```bash
# Create a new orphan branch
git checkout --orphan new-main

# Add all files
git add -A

# Commit without history
git commit -m "Initial commit - cleaned security issues"

# Force push
git branch -M main
git push -f origin main
```

## Prevention Measures

### 1. Update .env File (DONE ✅)

Your `.env` file is already in `.gitignore`. Keep it that way!

```bash
# Verify .env is ignored
git check-ignore .env  # Should output: .env
```

### 2. Use Git Hooks to Prevent Future Leaks

Install a pre-commit hook to scan for API keys:

```bash
# Install gitleaks (macOS)
brew install gitleaks

# Run a scan
gitleaks detect --source . --verbose

# Set up as pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
gitleaks protect --staged --verbose
EOF

chmod +x .git/hooks/pre-commit
```

### 3. GitHub Secret Scanning

If using GitHub:
1. Go to Settings → Code security and analysis
2. Enable "Secret scanning"
3. Enable "Push protection"

### 4. Rotate API Keys Regularly

- Set a calendar reminder to rotate API keys every 90 days
- Use Google Cloud Console to set key restrictions:
  - Restrict to specific APIs (Generative AI API only)
  - Add application restrictions (HTTP referrers or IP addresses)
  - Set usage quotas

## Verification Checklist

Before proceeding, verify:

- [ ] Old API key(s) revoked in Google Cloud Console
- [ ] New API key generated and stored in `.env` (never committed)
- [ ] `.env` file is in `.gitignore`
- [ ] Git history cleaned (using one of the methods above)
- [ ] Force push completed to update public repository
- [ ] Collaborators notified to re-clone repository
- [ ] Git hooks installed to prevent future leaks

## Additional Resources

- [Google Cloud - API Key Best Practices](https://cloud.google.com/docs/authentication/api-keys)
- [git-filter-repo Documentation](https://github.com/newren/git-filter-repo)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [Gitleaks - Secret Scanning](https://github.com/gitleaks/gitleaks)

## Support

If you need help with any of these steps, please:
1. Stop pushing to the public repository immediately
2. Revoke the exposed API keys first (most critical)
3. Seek assistance before proceeding with git history cleanup

---

**Remember:** Once an API key is exposed in a public repository, assume it has been compromised and revoke it immediately.
