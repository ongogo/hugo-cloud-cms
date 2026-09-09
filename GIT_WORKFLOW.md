# Git Workflow & Cloudflare Pages Deployment Guide

## Project Overview
- **Repository**: `https://github.com/ongogo/hugo-cloud-cms.git`
- **Branch**: `main`
- **Deployment**: GitHub Actions → Cloudflare Pages
- **Live Site**: https://note.ironnori.cc/
- **Working Directory**: `/Users/ongogo/Al-Projects/hugo-cloud-cms`

---

## Standard Commit & Push Workflow

### 1. Check Status
```bash
cd /Users/ongogo/Al-Projects/hugo-cloud-cms
git status
```

### 2. Stage Changes
```bash
# Stage specific file
git add content/bbc-english/YYYY-MM-DD-slug.md

# Or stage all changes
git add .
```

### 3. Commit
```bash
git commit -m "Add BBC Learning English - Series: Episode Title (ep-XXXXXX)"
```

### 4. Pull & Rebase (Handle Concurrent Edits)
```bash
git pull --rebase origin main
```

### 5. Push
```bash
git push origin main
```

### 6. Verify Deployment
- **GitHub Actions**: https://github.com/ongogo/hugo-cloud-cms/actions
- **Cloudflare Pages**: Check build logs in Cloudflare dashboard
- **Live Site**: https://note.ironnori.cc/ (updates within 2-5 minutes after successful build)

---

## Git Configuration (One-time Setup)

```bash
# Set identity for commits
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## Content Creation Template

### File Naming Convention
```
content/bbc-english/YYYY-MM-DD-series-episode-title.md
```

### Required Front Matter
```yaml
---
title: "BBC Learning English - Series: Episode Title"
date: YYYY-MM-DD
tags: ["BBC Learning English", "Series Name", "topic", "vocabulary", "LEVEL"]
audio_url: "https://downloads.bbc.co.uk/.../episode.mp3"  # or "" if none
level: "A2/B1/B2"
difficulty: "Easy/Intermediate/Upper Intermediate"
topic: "Topic keywords"
summary_zh: "中文摘要..."
source_url: "https://www.bbc.co.uk/learningenglish/..."
---
```

### Download Links Section
```markdown
🔗 **下载链接**:
- [MP3 音频](https://downloads.bbc.co.uk/.../episode.mp3)
- [PDF 练习册](https://downloads.bbc.co.uk/.../worksheet.pdf)
- [PDF 文字稿](https://downloads.bbc.co.uk/.../transcript.pdf)
```

---

## Applying Bundle/Patch Files (Alternative to Direct Push)

If the sandbox environment cannot push directly, use these methods:

### Method 1: Git Bundle
```bash
# On the machine with the bundle
git clone /path/to/repo.bundle temp-clone
cd temp-clone
git checkout content/site-hygiene-and-seo-fixes

# In your main repo
git fetch /path/to/repo.bundle content/site-hygiene-and-seo-fixes:content/site-hygiene-and-seo-fixes
git checkout content/site-hygiene-and-seo-fixes
```

### Method 2: Git Patch
```bash
# Apply patch
git apply /path/to/changes.patch

# Or with 3-way merge for conflicts
git apply --3way /path/to/changes.patch
```

### Method 3: Manual Cherry-pick
```bash
# Add remote pointing to the other repo
git remote add temp-repo /path/to/other/repo
git fetch temp-repo
git cherry-pick <commit-hash>
```

---

## Cloudflare Pages Configuration

### Build Settings (auto-detected from Hugo)
- **Build Command**: `hugo --minify`
- **Output Directory**: `public`
- **Hugo Version**: Latest (specified in GitHub Actions)

### Environment Variables (if needed)
```yaml
# In Cloudflare Pages dashboard > Settings > Environment Variables
HUGO_VERSION: "latest"
```

### Custom Domain
- **Primary**: note.ironnori.cc
- **DNS**: CNAME pointing to Cloudflare Pages domain

---

## Troubleshooting

### Push Rejected (Non-fast-forward)
```bash
git pull --rebase origin main
# Resolve conflicts if any
git push origin main
```

### Authentication Issues
```bash
# Use SSH (if configured)
git remote set-url origin git@github.com:ongogo/hugo-cloud-cms.git

# Or use Personal Access Token
git remote set-url origin https://<TOKEN>@github.com/ongogo/hugo-cloud-cms.git
```

### Build Failures
1. Check GitHub Actions logs
2. Common issues:
   - Missing front matter fields
   - Invalid YAML syntax
   - Hugo template errors
   - Broken markdown links

### Local Preview Before Push
```bash
hugo server -D
# Visit http://localhost:1313
```

---

## Episode Processing Checklist

For each new BBC Learning English episode:

- [ ] Navigate to episode URL
- [ ] Extract full text content (`document.body.innerText`)
- [ ] Find MP3 URL (`document.querySelectorAll('a[href$=".mp3"]')`)
- [ ] Find PDF URLs (`document.querySelectorAll('a[href$=".pdf"]')`)
- [ ] Create markdown file with template
- [ ] Write to `content/bbc-english/`
- [ ] Add, commit, pull --rebase, push
- [ ] Verify GitHub Actions build passes
- [ ] Confirm live at https://note.ironnori.cc/

---

## Directory Structure
```
hugo-cloud-cms/
├── content/
│   └── bbc-english/           # All episode markdown files
├── static/                    # Static assets
├── layouts/                   # Hugo templates
├── .github/
│   └── workflows/             # GitHub Actions for deployment
├── hugo.toml                  # Hugo configuration
└── GIT_WORKFLOW.md            # This file
```

---

## Useful Commands Reference

```bash
# View recent commits
git log --oneline -10

# View current branch
git branch -v

# Check remote
git remote -v

# Show diff before commit
git diff

# Amend last commit message
git commit --amend -m "New message"

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Stash changes temporarily
git stash
git stash pop
```

---

## Security Notes

- **Never commit** API keys, tokens, or credentials
- Use GitHub Secrets for sensitive deployment values
- Keep `.gitignore` updated for local-only files
- Review GitHub Actions permissions periodically

---

## Last Updated
- **Date**: 2026-09-08
- **Maintainer**: ongogo
- **Repository**: ongogo/hugo-cloud-cms