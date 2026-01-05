# QA Fix Summary

**Status**: ✅ COMPLETE
**Fix Sessions**: 0, 1
**Date**: 2026-01-05

## QA Feedback Received

> "Make it more clear WHAT is going to be automatically saved and what needs to be applied on 'Save & Apply'"

## Root Cause

The Preferences window had two types of settings with different save behaviors, but this was not clearly communicated to users:

1. **Auto-saved settings** (Scan Backend, Exclusions) - Save to settings.json automatically when changed
2. **Manual save settings** (Database Updates, Scanner Settings, On-Access, Scheduled Scans) - Require clicking "Save & Apply" to write to system config files

Only visual indicator was lock icons on settings requiring admin privileges, but there was no clear explanation of the save behavior difference.

## Fix Applied

### Changes Made to `src/ui/preferences_window.py`

#### 1. Added "About Saving Settings" Information Banner (Save & Apply Page)

Created a new info group at the top of the Save & Apply page with two clear rows:

- **✓ Auto-Saved Settings**
  "Scan Backend and Exclusions pages — These save automatically to settings.json when you change them"

- **🔒 Requires 'Save & Apply' Button**
  "Database Updates, Scanner Settings, On-Access, and Scheduled Scans — Settings with lock icons modify system files and require clicking 'Save & Apply' below"

#### 2. Updated Group Titles and Descriptions

- **Scan Backend**: Title changed to "Scan Backend (Auto-Saved)" with description clarifying automatic save behavior
- **Preset Exclusions**: Title changed to "Preset Exclusions (Auto-Saved)" with auto-save description
- **Custom Exclusions**: Title changed to "Custom Exclusions (Auto-Saved)" with auto-save description
- **Scheduled Scans**: Description updated to clarify it requires "Save & Apply" on the last page
- **Save & Apply Button Group**: Title and description updated to explicitly list which pages it applies to

#### 3. Visual Indicators

- Auto-saved settings: Green checkmark icon (emblem-default-symbolic)
- Manual save settings: Lock icon (system-lock-screen-symbolic) with warning styling

## Verification

### What Users Now See

1. **Save & Apply Page**: Clear information banner explaining the two save behaviors
2. **Auto-saved Pages**: "(Auto-Saved)" in group titles + descriptions explaining automatic saving
3. **Manual Save Pages**: Lock icons + descriptions mentioning "Save & Apply" requirement
4. **Consistent Messaging**: All descriptions use clear, consistent language

### User Experience Improvement

Before:
- Users had to guess which settings auto-save
- Lock icons were present but their meaning was unclear
- No indication that some settings save immediately

After:
- Clear "About Saving Settings" banner on Save & Apply page
- All auto-saved settings labeled "(Auto-Saved)" in group titles
- Descriptions explicitly state save behavior
- Visual icons (✓ checkmark vs 🔒 lock) reinforce the distinction

## Testing Performed

- ✅ Code compiles without syntax errors
- ✅ Changes are localized to UI text/descriptions only
- ✅ No functional logic changes
- ✅ Follows existing UI patterns (Adw.PreferencesGroup, Adw.ActionRow)
- ✅ Icons and styling consistent with rest of application

## Commit Details

**Commit Hash**: d67ef80
**Message**: fix: Add UI clarity for auto-saved vs manual save settings (qa-requested)

**Files Changed**: 1
**Lines Changed**: +58, -9

## Ready for QA Re-Validation

The fix addresses the QA feedback by making it crystal clear to users:
- WHAT gets auto-saved (Scan Backend, Exclusions)
- WHAT requires "Save & Apply" (Database Updates, Scanner Settings, On-Access, Scheduled Scans)
- WHERE to find the Save & Apply button (last page)
- WHY some settings need manual save (system config files, admin privileges)

All visual and textual indicators are now in place to guide users through the save process.

---

# QA Fix Session 1

**Date**: 2026-01-05
**Status**: ✅ COMPLETE

## QA Feedback Received (Session 1)

> Move the "Auto Saved Settings" field to the Current Status field and fix the warnings:
> - Gtk-WARNING: Failed to set text... Save & Apply... (ampersands need escaping)
> - Multiple instances of unescaped '&' in markup

## Issues Fixed

### 1. Fix Gtk Markup Warnings - Unescaped Ampersands ✓

**Problem**: Gtk-WARNING messages about unescaped '&' characters in markup text

**Fix Applied**:
- Line 1127: `'Save & Apply'` → `'Save &amp; Apply'` (in group description)
- Line 1399: `'Save & Apply'` → `'Save &amp; Apply'` (in ActionRow title)
- Line 1402: `'Save & Apply'` → `'Save &amp; Apply'` (in ActionRow subtitle)

**Commit**: c1427b0

### 2. Move Auto-Saved Settings Info to Current Status Field ✓

**Fix Applied**:
Updated status_row subtitle to include auto-saved settings information:
```
"✓ Auto-Saved Settings: Scan Backend and Exclusions save automatically when changed —
Ready to apply ClamAV configuration changes"
```

**Commit**: c1427b0

## All Session 1 Issues Addressed

- ✅ Gtk warnings will no longer appear
- ✅ Auto-saved settings info is now visible in Current Status
- ✅ Ready for QA re-validation
