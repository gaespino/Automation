# Debug Framework Release Process Template

**Version:** 1.0
**Last Updated:** February 18, 2026
**Purpose:** Standardized process for generating release notes and update emails for Debug Framework (S2T/DebugFramework)

---

## 📋 QUICK REFERENCE

**Timeline:** Start 1-2 weeks before release
**Duration:** ~2-4 hours for research and documentation
**Output:** Release tracking document + formatted email
**Frequency:** After each significant update/deployment cycle

**Process Flow:**
```
Deployment Reports → Categorize Changes → Write Documentation → Draft Email → Review → Send → Archive
```

---

## PHASE 1: PRE-RELEASE RESEARCH (1-2 Weeks Before)

### Step 1.1: Gather Deployment Data

**Location:** `DEVTOOLS/deployment_report_*.csv`

**Actions:**
1. Identify all deployment reports since last release date
2. Filter by date range (e.g., Jan 22 - Feb 18)
3. Note the pattern: `deployment_report_YYYYMMDD_HHMMSS.csv`

**Command to list recent reports:**
```powershell
Get-ChildItem DEVTOOLS\deployment_report_*.csv | Where-Object {$_.LastWriteTime -gt "2026-01-22"} | Sort-Object LastWriteTime
```

**What to extract:**
- Deployed files and their paths
- Product (GNR/CWF/DMR)
- Similarity scores (indicates magnitude of change)
- New files vs modifications

---

### Step 1.2: Review Change Documentation

**Files to check:**
- `DEVTOOLS/CHANGELOG.md` - Structured change log
- `DEVTOOLS/UPDATE_NOTES_*.md` - Feature-specific notes
- `DEVTOOLS/*_GUIDE.md` - Documentation updates

**Search for:**
- Version numbers
- Date stamps
- "NEW", "ADDED", "FIXED", "UPDATED" markers

---

### Step 1.3: Search Source Code for Change Markers

**Repositories to scan:**
- `S2T/BASELINE/` (GNR/CWF)
- `S2T/BASELINE_DMR/` (DMR)

**Common markers in comments:**
```python
# NEW - [date or description]
# FIXED - [issue description]
# ADDED - [feature description]
# UPDATED - [date]
# TODO - [pending items]
```

**Search command:**
```powershell
# Search for commented changes
Select-String -Path "S2T\BASELINE\**\*.py" -Pattern "# (NEW|FIXED|ADDED|UPDATED)" -Context 0,2

# Search for dated comments (2026)
Select-String -Path "S2T\BASELINE\**\*.py" -Pattern "202[56]" -Context 0,2
```

**Key areas to check:**
- `DebugFramework/UI/*.py` - UI changes
- `DebugFramework/ExecutionHandler/*.py` - Execution logic
- `S2T/*.py` - Core S2T functionality
- `S2T/Tools/*.py` - New tools
- `DebugFramework/*/README*.md` - Documentation

---

### Step 1.4: Identify New Files

**Method 1: File comparison**
```powershell
# Compare with backup or previous release
$baseline = Get-ChildItem -Path "S2T\BACKUPS\[previous_date]" -Recurse -File
$current = Get-ChildItem -Path "S2T\BASELINE" -Recurse -File
Compare-Object $baseline $current -Property Name
```

**Method 2: Check deployment reports**
- Look for "NEW FILE" or 0% similarity in deployment reports

**Common locations for new files:**
- `S2T/Tools/` - New utilities
- `DebugFramework/Automation_Flow/` - Flow components
- `S2T/DOCUMENTATION/*/` - New documentation
- `S2T/product_specific/*/` - Product-specific code

---

### Step 1.5: Check Documentation Updates

**Files to review:**
- `S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/README.md`
- `S2T/DOCUMENTATION/DEBUG_FRAMEWORK_S2T/*_GUIDE.md`
- Any `*.md` files in BASELINE or BASELINE_DMR

**Look for:**
- Version numbers in headers
- "Last updated" dates
- New sections or features documented
- Installation/setup changes

---

## PHASE 2: CHANGE CATEGORIZATION

### Step 2.1: Organize Changes by Type

Create a spreadsheet or markdown table:

| Category | Change Description | Product | Files Affected | Priority |
|----------|-------------------|---------|----------------|----------|
| 🆕 NEW FEATURE | Automated installer | All | installation/* | HIGH |
| 🐛 BUG FIX | Progress calculation | All | ControlPanel.py | MEDIUM |
| 📈 IMPROVEMENT | Thread state tracking | All | ThreadsHandler.py | MEDIUM |
| 📚 DOCUMENTATION | MDT Tools guide | DMR | MDT_TOOLS_*.md | LOW |

**Category Icons:**
- 🆕 NEW FEATURE - Brand new functionality
- 🐛 BUG FIX - Fixes for existing issues
- 📈 IMPROVEMENT - Enhancements to existing features
- 📚 DOCUMENTATION - Documentation updates
- 🔧 TOOLS - Developer/deployment tools

---

### Step 2.2: Tag by Product

Use consistent tags:
- `[Common]` - Applies to all products (GNR/CWF/DMR)
- `[GNR/CWF]` - Granite Rapids and Clearwater Forest only
- `[DMR]` - Diamond Rapids only
- `[GNR]` - Granite Rapids only
- `[CWF]` - Clearwater Forest only

**Example:**
```
🆕 NEW FEATURE: Automated Installer [Common]
🆕 NEW FEATURE: MDT Tools Interface [DMR Primary, GNR/CWF Support]
🆕 NEW FEATURE: MaskEditor CBB Architecture [DMR Only]
```

---

### Step 2.3: Prioritize for Email

**HIGH Priority** (Must mention in email):
- New user-facing features
- Major bug fixes affecting workflow
- Breaking changes or API changes
- Security updates
- Installation/setup changes

**MEDIUM Priority** (Mention if space permits):
- Minor bug fixes
- Performance improvements
- Enhanced error messages
- Documentation updates

**LOW Priority** (Track but don't highlight):
- Code refactoring
- Internal optimizations
- Developer tools
- Minor documentation fixes

---

## PHASE 3: DOCUMENT GENERATION

### Step 3.1: Create Release Tracking Document

**Filename:** `DEVTOOLS/deploys/RELEASE_v[VERSION]_[MONTH][YEAR].md`
**Example:** `RELEASE_v1.7.1_Feb2026.md`

**Template Structure:**
```markdown
# Debug Framework Release v[VERSION] - [MONTH YEAR]

## Release Information
- Version: [VERSION]
- Release Date: [DATE]
- Previous Version: [PREV_VERSION] ([PREV_DATE])
- Products: GNR, CWF, DMR
- Repositories: BASELINE (GNR/CWF), BASELINE_DMR (DMR)

## Overview
[2-3 sentence summary of release highlights]

## 🆕 NEW FEATURES
### 1. [Feature Name] [Product Tags]
**Version:** [Version if applicable]
**Location:** `path/to/file`
[Description with key points as bullets]

## 🐛 BUG FIXES
### 1. [Fix Description] [Product Tags]
**Files Modified:** `path/to/file`
**Issues Fixed:** [List issues]
**Impact:** [User impact]

## 📈 IMPROVEMENTS
[List improvements]

## 📚 DOCUMENTATION UPDATES
[List new/updated docs]

## 📦 DEPLOYMENT REPORTS
[Summary of deployment_report_*.csv files]

## 🔍 STRUCTURAL DIFFERENCES: BASELINE vs BASELINE_DMR
[Note major differences]

## 📊 VERSION HISTORY
[Table of versions]

## 🚀 UPGRADE INSTRUCTIONS
[Step-by-step upgrade process]

## 📞 SUPPORT
[Contact information]

## 📝 NOTES
[Additional notes, import examples, etc.]
```

---

### Step 3.2: Create Email Draft

**Filename:** `DEVTOOLS/deploys/RELEASE_EMAIL_v[VERSION]_[MONTH][YEAR].md`

**Template Structure:**
```markdown
Subject: Debug Framework v[VERSION] Release - [Key Features Summary]

Hi Team,

Debug Framework release v[VERSION] is ready and updated in all supported
product repositories (GNR / CWF / DMR). [1-2 sentence overview].
Please update your system repository to include the latest version.

## 🆕 NEW FEATURES

### **[Feature 1]** – [Product Tags]
- [Key point 1]
- [Key point 2]
- **Location:** `path/to/feature`

**Quick Start:**
```bash
[command or code example]
```

[Repeat for 3-5 top features]

## 🐛 BUG FIXES
[List top 3-5 fixes with checkmarks]
✅ [Fix 1]
✅ [Fix 2]

## 📚 DOCUMENTATION
| Documentation | Link |
|---------------|------|
| [Doc name] | [URL] |

## 🚀 UPGRADE INSTRUCTIONS
1. Update repository
2. Run installer (if applicable)
3. Verify installation

## 📋 PRODUCT IMPORT EXAMPLES
[Code blocks for GNR/CWF/DMR]

## 🔧 THR DEBUG TOOLS
[Table of available tools]

## 🎯 HIGHLIGHTS OF THIS RELEASE
✅ [Highlight 1]
✅ [Highlight 2]

## 📞 SUPPORT
Any questions or issues with the update, feel free to contact me.

Best regards,
[Name]
```

---

### Step 3.3: Quality Checklist

- [ ] All major features documented
- [ ] File paths use correct format: `path/to/file.py` or `[file.py](path/file.py)`
- [ ] Product tags consistent: [Common], [GNR/CWF], [DMR]
- [ ] Version numbers accurate
- [ ] Dates formatted consistently (Month DD, YYYY)
- [ ] Code examples tested and accurate
- [ ] Documentation links valid
- [ ] Import examples correct for each product
- [ ] No sensitive information (credentials, internal URLs)
- [ ] Spelling and grammar checked
- [ ] Icons/emojis used consistently

---

## PHASE 4: EMAIL PREPARATION

### Step 4.1: Convert Markdown to Email Format

**Options:**
1. **Copy directly from .md file** (if email client supports markdown)
2. **Use markdown preview** (VS Code preview → copy rendered HTML)
3. **Use converter tool** (e.g., pandoc)

**Command for HTML conversion:**
```powershell
pandoc RELEASE_EMAIL_v1.7.1_Feb2026.md -f markdown -t html -s -o release_email.html
```

---

### Step 4.2: Add Visual Elements (Optional)

**Consider adding:**
- Screenshots of new UI features
- Architecture diagrams (e.g., MaskEditor comparison)
- Flow charts (e.g., installation process)
- Before/After comparisons

**Tools:**
- PowerPoint for diagrams
- Snipping Tool for screenshots
- Draw.io for flow charts

**Best practices:**
- Keep images under 500KB each
- Use PNG for screenshots, JPG for photos
- Annotate images with arrows/labels
- Provide alt text for accessibility

---

### Step 4.3: Email Formatting Tips

**Subject Line:**
- Format: `Debug Framework v[VERSION] Release - [Key Features]`
- Keep under 60 characters if possible
- Highlight 1-2 most exciting features
- Example: `Debug Framework v1.7.1 - Automated Installer & MDT Tools`

**Body Structure:**
- Use **bold** for feature names
- Use bullet points (•) or checkmarks (✅) for lists
- Keep paragraphs short (2-3 sentences max)
- Use tables for structured data
- Add horizontal rules (---) to separate major sections

**Tone:**
- Professional but approachable
- Focus on user benefits, not technical details
- Use active voice ("This release introduces..." not "Introduced are...")
- Celebrate achievements ("excited to announce", "pleased to share")

---

## PHASE 5: REVIEW & APPROVAL

### Step 5.1: Self-Review

**Technical Accuracy:**
- [ ] Version numbers correct
- [ ] File paths exist and accurate
- [ ] Code examples run without errors
- [ ] Product tags match actual implementation
- [ ] Documentation links accessible

**Clarity:**
- [ ] Features explained in user terms
- [ ] Jargon minimized or explained
- [ ] Benefits clear (not just features)
- [ ] Instructions actionable

**Completeness:**
- [ ] All major changes covered
- [ ] Breaking changes highlighted
- [ ] Upgrade path clear
- [ ] Support contact included

---

### Step 5.2: Peer Review (Optional)

**Ask colleague to review:**
- Is it clear what's new?
- Would they know how to upgrade?
- Are there any confusing sections?
- Any missing critical information?

---

### Step 5.3: Test Checklist

- [ ] Test all code examples
- [ ] Verify all file paths exist
- [ ] Click all documentation links
- [ ] Test installation instructions on clean system
- [ ] Verify import examples work for each product

---

## PHASE 6: DISTRIBUTION

### Step 6.1: Send Email

**Recipients:**
- Product teams (GNR, CWF, DMR)
- Validation teams
- FAE teams
- Management (if major release)

**Timing:**
- Send early in work week (Tuesday-Thursday ideal)
- Avoid Friday releases (support issues over weekend)
- Consider time zones for global teams

---

### Step 6.2: Archive Documentation

**Actions:**
1. **Move deployment reports to archive:**
   ```powershell
   New-Item -ItemType Directory -Path "DEVTOOLS\deploys\archives\$(Get-Date -Format 'yyyy-MM')"
   Move-Item "DEVTOOLS\deployment_report_202602*.csv" "DEVTOOLS\deploys\archives\2026-02\"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [1.7.1] - 2026-02-19
   ### Added
   - Automated GUI installer
   - MDT Tools interface
   ### Fixed
   - Progress calculation bug
   ```

3. **Tag release in version control:**
   ```bash
   git tag -a v1.7.1 -m "Release v1.7.1 - Automated Installer & MDT Tools"
   git push origin v1.7.1
   ```

---

### Step 6.3: Follow-Up

**1 day after:**
- Monitor for questions/issues
- Respond promptly to feedback

**1 week after:**
- Send reminder email if needed
- Update FAQs based on questions received

**Next release:**
- Use this release document as "Previous Version" reference

---

## PHASE 7: AUTOMATION OPPORTUNITIES

### Optional: Generate Release Notes Script

**Location:** `DEVTOOLS/generate_release_notes.py`

**Functionality:**
- Parse deployment_report_*.csv in date range
- Search for code markers (# NEW, # FIXED, etc.)
- Extract version numbers from docs
- Generate markdown template with file lists
- **NEW:** Generate HTML version automatically

**Usage:**
```powershell
# Generate markdown draft only
python DEVTOOLS\generate_release_notes.py --start-date 2026-01-22 --end-date 2026-02-18 --output DEVTOOLS\deploys\DRAFT_RELEASE.md

# Generate markdown + HTML version
python DEVTOOLS\generate_release_notes.py --start-date 2026-01-22 --end-date 2026-02-18 --html
```

**HTML Generation:**
- Use `--html` flag to automatically generate HTML version
- Uses markdown converter from `OtherFiles/MarkdownConverter/`
- HTML saved in `deploys/release_files/` (git-ignored)
- Ready for email distribution or PDF creation (browser print)

**See:** `DEVTOOLS/generate_release_notes.py` for implementation

---

## TIPS & BEST PRACTICES

### DO:
✅ Start early (1-2 weeks before release)
✅ Focus on user impact, not code changes
✅ Use consistent formatting and naming
✅ Provide working code examples
✅ Include upgrade instructions
✅ Test all links and examples
✅ Highlight security updates prominently
✅ Use product tags consistently

### DON'T:
❌ Wait until release day to start documentation
❌ Copy/paste error messages without context
❌ Use internal jargon without explanation
❌ Forget to document breaking changes
❌ Include sensitive information (credentials, private repos)
❌ Overwhelm with too much technical detail
❌ Skip testing code examples

---

## TEMPLATE FILES

**Available in this folder:**
- `RELEASE_v1.7.1_Feb2026.md` - Example release tracking doc
- `RELEASE_EMAIL_v1.7.1_Feb2026.md` - Example email draft
- `RELEASE_TEMPLATE.md` - This file (process guide)
- Future: `generate_release_notes.py` - Automation script

---

## VERSIONING CONVENTIONS

**Version Format:** `vMAJOR.MINOR.PATCH`

- **MAJOR** (v2.0, v3.0) - Breaking changes, major architecture updates
- **MINOR** (v1.7, v1.8) - New features, backwards compatible
- **PATCH** (v1.7.1, v1.7.2) - Bug fixes, minor updates

**Release Naming:**
- Development releases: `v2.0-dev`, `v2.0-beta`
- Production releases: `v2.0`, `v1.7.1`
- Hotfixes: `v1.7.1-hotfix1`

---

## REFERENCES

**Documentation:**
- [Markdown Guide](https://www.markdownguide.org/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

**Internal:**
- Previous releases in `DEVTOOLS/deploys/`
- Framework documentation in `S2T/DOCUMENTATION/`
- Deployment manifests in `DEVTOOLS/deployment_manifest_*.json`

---

## CHANGELOG

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Feb 18, 2026 | Initial template created based on v1.7.1 release process |

---

**Document Owner:** THR Debug Framework Team
**Last Review:** February 18, 2026
**Next Review:** After next major release
