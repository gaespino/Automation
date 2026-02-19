# Quick Release Notes Generation - Copilot Skill

**Purpose:** Generate complete release notes and email drafts for Debug Framework releases
**Time Required:** 5-10 minutes (mostly automated)
**Last Updated:** February 18, 2026

---

## 🚀 QUICK START (For AI/Copilot)

When asked to generate release notes, follow this process:

### Step 1: Gather Information from User

Ask the user for:
- **Last release date** (e.g., "2026-01-22")
- **New version number** (e.g., "1.7.1" or "2.1")
- **Any specific features/fixes to highlight** (optional - will be auto-detected)

### Step 2: Run the Automated Script

```powershell
cd C:\Git\Automation\DEVTOOLS
python generate_release_notes.py --start-date YYYY-MM-DD --version X.X.X --html
```

This generates:
- `deploys/DRAFT_RELEASE_vX.X.X_MonYYYY.md` - Full tracking document
- `deploys/DRAFT_RELEASE_vX.X.X_MonYYYY.html` - HTML version

### Step 3: Research Additional Context

Run semantic searches to find:
- New features since last release date
- Documentation updates (*.md files modified since last release)
- Known issues or pending fixes
- Product-specific changes (GNR/CWF/DMR)

**Search queries:**
- "new features documentation updated since [date]"
- "bug fixes improvements changes [product]"
- "installation setup configuration changes"
- "known issues workarounds pending"

### Step 4: Structure the Full Release Document

Create: `deploys/RELEASE_v[VERSION]_[MONTH][YEAR].md`

**Template structure:**
```markdown
# Debug Framework Release v[VERSION] - [MONTH YEAR]

## Release Information
- Version: [VERSION]
- Release Date: [DATE]
- Previous Version: [PREV_VERSION]
- Products: GNR, CWF, DMR
- Repositories: BASELINE (GNR/CWF), BASELINE_DMR (DMR)

## Overview
[2-3 sentence summary]

## 🆕 NEW FEATURES
[Organized by Common/GNR/CWF/DMR with subsections]

## 🐛 BUG FIXES
[List fixes with file locations and impact]

## 📈 IMPROVEMENTS
[Enhancement details]

## 📚 DOCUMENTATION UPDATES
[New and updated docs with GitHub links]

## 📦 DEPLOYMENT REPORTS
[Recent deployment summaries]

## ⚠️ KNOWN ISSUES
[Current issues with workarounds]

## 📊 VERSION HISTORY
[Version table]

## 🚀 UPGRADE INSTRUCTIONS
[Step-by-step upgrade process]

## 📞 SUPPORT
[Contact information]
```

### Step 5: Create Email Draft

Create: `deploys/RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].md`

**Critical: Use inverted pyramid structure:**
1. **Subject line** - Version + key features
2. **Greeting** - Brief intro (1-2 sentences)
3. **🎯 HIGHLIGHTS** - Bullet list of 10-12 key points (MOST IMPORTANT - comes first!)
4. **🚀 UPGRADE INSTRUCTIONS** - What to do NOW (3 steps)
5. **🆕 NEW FEATURES** - Detailed descriptions
6. **🐛 UPDATES/FIXES** - Organized by product
7. **⚠️ KNOWN ISSUES** - Issues and workarounds
8. **📚 DOCUMENTATION** - Links table
9. **📋 PRODUCT IMPORT EXAMPLES** - Code snippets
10. **🔧 THR DEBUG TOOLS** - Available tools
11. **📞 SUPPORT** - Contact info

**Highlights format:**
```markdown
## 🎯 HIGHLIGHTS OF THIS RELEASE

✅ **[Benefit]** - [One-line description with impact]
✅ **[Feature]** - [User-facing improvement]
[10-12 highlights total]
```

### Step 6: Generate HTML/PDF

```powershell
cd C:\Git\Automation\OtherFiles\MarkdownConverter
python md_converter.py "C:\Git\Automation\DEVTOOLS\deploys\RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].md" -f html -o "C:\Git\Automation\DEVTOOLS\deploys\release_files\RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].html"
```

For PDF: Open HTML in browser → Ctrl+P → Save as PDF

### Step 7: Update Supporting Files

1. **Update .gitignore** if needed:
   ```
   deploys/release_files/
   ```

2. **Update RELEASE_TEMPLATE.md** if process changed

3. **Create helper batch file** (optional):
   ```batch
   @echo off
   start "" "C:\Git\Automation\DEVTOOLS\deploys\release_files\RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].html"
   ```

---

## 📋 CHECKLIST FOR COMPLETE RELEASE

- [ ] Run `generate_release_notes.py` with correct dates and version
- [ ] Review auto-generated draft for accuracy
- [ ] Research additional features/fixes not auto-detected
- [ ] Create full tracking document (RELEASE_v[VERSION]_[MONTH][YEAR].md)
- [ ] Create email draft (RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].md)
- [ ] Verify all GitHub documentation links work
- [ ] Mark NEW features with ⭐ NEW or ⭐ in tables
- [ ] Organize highlights with most important first
- [ ] Generate HTML version
- [ ] Test HTML in browser
- [ ] Create PDF if needed (browser print)
- [ ] Verify all product tags [Common], [GNR/CWF], [DMR]
- [ ] Check version numbers are consistent
- [ ] Update KNOWN ISSUES section if applicable

---

## 🎯 KEY PRINCIPLES

### Documentation Links
- **ALWAYS use GitHub URLs**, never local paths
- Format: `https://github.com/gaespino/Automation/blob/main/[path]`
- Examples:
  ```markdown
  [INSTALLATION_GUIDE.md](https://github.com/gaespino/Automation/blob/main/S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/INSTALLATION_GUIDE.md)
  ```

### Feature Organization
- **[Common]** - All products (GNR/CWF/DMR)
- **[GNR/CWF]** - Granite Rapids and Clearwater Forest
- **[DMR]** - Diamond Rapids only
- **[GNR]**, **[CWF]** - Single product

### NEW Feature Markers
Use ⭐ NEW for features added since last release:
- In feature headers: `### **Feature Name** – DMR ⭐ NEW`
- In tables: `| **Tool Name** ⭐ NEW | Description |`
- In lists: `- ✅ **New Feature** - Description`

### Highlights Best Practices
- Lead with USER BENEFIT, not technical details
- Use action verbs: "Faster", "Enhanced", "Improved"
- Quantify when possible: "30+ minutes to 5 minutes"
- Keep to 10-12 highlights maximum
- Most impactful items first

### Email Structure
- **TLDR first** - Highlights and upgrade instructions at top
- **Details second** - Features, fixes, documentation
- **Reference last** - Tools, examples, support
- Assume readers won't scroll past highlights

---

## 🔍 RESEARCH QUERIES FOR AI

When generating release notes, use these searches:

### Find New Features
```
Search: "new features added since [last_release_date]"
Folders: S2T/BASELINE, S2T/BASELINE_DMR
Look for: *.py files with # NEW, # ADDED comments
```

### Find Bug Fixes
```
Search: "# FIXED|# BUG|fixed issue|resolved"
Folders: DebugFramework/UI, S2T/
Look for: Recent commits, # FIXED comments
```

### Find Documentation Updates
```
Files: **/*.md
Modified since: [last_release_date]
Especially: S2T/DOCUMENTATION/**, **/README.md
```

### Find Deployment Reports
```
Files: DEVTOOLS/deployment_report_*.csv
Date range: [last_release_date] to [today]
Parse for: New files, significant changes (<80% similarity)
```

### Product-Specific Changes
```
GNR/CWF: S2T/BASELINE/
DMR: S2T/BASELINE_DMR/
Look for: Architecture changes, new tools, configuration updates
```

---

## 📝 EXAMPLE PROMPTS FOR FUTURE SESSIONS

### Simple Request
```
"Generate release notes for version 1.8.0, last release was January 22, 2026"
```

### Detailed Request
```
"Create release notes for Debug Framework v1.8.0. Last release was v1.7.1 on
February 19, 2026. Focus on new DMR features and bug fixes. Include HTML version."
```

### Quick Update
```
"Update release notes to include: [specific feature]. Add to NEW FEATURES section
and highlights."
```

---

## 🛠️ AUTOMATION COMMANDS

### Generate Draft (Markdown + HTML)
```powershell
cd C:\Git\Automation\DEVTOOLS
python generate_release_notes.py --start-date 2026-01-22 --version 1.8.0 --html
```

### Convert Email to HTML
```powershell
cd C:\Git\Automation\OtherFiles\MarkdownConverter
python md_converter.py "[email_md_path]" -f html -o "[output_html_path]"
```

### Check Git Status (What's not ignored)
```powershell
cd C:\Git\Automation\DEVTOOLS
git add -n deploys/
```

### Open Release Files Folder
```powershell
explorer C:\Git\Automation\DEVTOOLS\deploys\release_files\
```

---

## 📚 REFERENCE FILES

| File | Purpose | Location |
|------|---------|----------|
| **RELEASE_TEMPLATE.md** | Complete process guide | DEVTOOLS/deploys/ |
| **generate_release_notes.py** | Automation script | DEVTOOLS/ |
| **QUICKSTART_RELEASE.md** | This file (quick reference) | DEVTOOLS/deploys/ |
| **Example Release** | v1.7.1 full example | DEVTOOLS/deploys/RELEASE_v1.7.1_Feb2026.md |
| **Example Email** | v1.7.1 email example | DEVTOOLS/deploys/RELEASE_EMAIL_v1.7.1_Feb2026.md |

---

## 🎓 LEARNING FROM PAST RELEASES

### v1.7.1 (Feb 2026) - Key Lessons

**What Worked Well:**
- ✅ Inverted pyramid structure (highlights first)
- ✅ HTML generation for easy distribution
- ✅ Product-specific tagging [Common], [DMR], etc.
- ✅ GitHub links instead of local paths
- ✅ Known Issues section transparency
- ✅ Comprehensive highlights (11 items)

**What Was Added During Process:**
- X4 chop support details (from user notes)
- ATE configuration documentation
- DFF data collection interfaces
- Fuse File Generator marked as NEW
- Known issues section with workarounds

**Structure Improvements:**
- Moved highlights to top of email (TLDR first)
- Added upgrade instructions early
- Grouped fixes by product (DMR Only, All Products)
- Included code examples in features

---

## 💡 TIPS FOR AI ASSISTANTS

### When User Requests Release Notes:

1. **Always confirm key details first:**
   - Last release date
   - New version number
   - Target release date
   - Any specific highlights to include

2. **Use automation first:**
   - Run generate_release_notes.py
   - Review deployment reports
   - Search for documentation updates

3. **Structure matters:**
   - Email: TLDR first (highlights + upgrade)
   - Tracking doc: Comprehensive details
   - Always generate both

4. **Link hygiene:**
   - GitHub URLs only, never local paths
   - Test format: `[text](https://github.com/...)`
   - Don't wrap file links in backticks

5. **Version consistency:**
   - Check version in all files
   - Update version history table
   - Match subject line version

6. **HTML generation:**
   - Always offer HTML version
   - Use markdown converter
   - Save to release_files/ (git-ignored)

7. **Verify before finishing:**
   - All links work
   - Version numbers consistent
   - NEW markers on new features
   - Product tags correct
   - HTML renders properly

---

## 🔄 CONTINUOUS IMPROVEMENT

After each release:
- Update this QUICKSTART if process changed
- Add lessons learned
- Update example version numbers in prompts
- Document any new automation
- Note common issues encountered

---

**For AI:** This document serves as your "skill" for generating release notes. Follow the steps, use the structure, apply the principles. The examples in RELEASE_v1.7.1_Feb2026.md and RELEASE_EMAIL_v1.7.1_Feb2026.md show the expected output quality.

**Last Release:** v1.7.1 (February 19, 2026)
**Next Release:** Use this guide!
