/* app.js – TP Migration Tool */

// -----------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------

function val(id) {
  const el = document.getElementById(id);
  return el ? el.value.trim() : '';
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('applyToast');
  const msg   = document.getElementById('toastMsg');
  if (!toast || !msg) return;
  msg.textContent = message;
  toast.className = `toast align-items-center text-bg-${type} border-0`;
  const bsToast = bootstrap.Toast.getOrCreateInstance(toast, { delay: 4000 });
  bsToast.show();
}

// -----------------------------------------------------------------------
// Browse (native file dialog via Flask endpoint)
// -----------------------------------------------------------------------

function browse(inputId, type = 'folder') {
  fetch(`/browse?type=${type}`)
    .then(r => r.json())
    .then(d => {
      if (d.path) {
        const el = document.getElementById(inputId);
        if (el) el.value = d.path;
      }
    })
    .catch(() => showToast('Could not open file dialog.', 'danger'));
}

// -----------------------------------------------------------------------
// Select-all toggle for a section
// -----------------------------------------------------------------------

function toggleAll(section, checked) {
  document.querySelectorAll(`.${section}-check`).forEach(cb => {
    cb.checked = checked;
  });
}

// -----------------------------------------------------------------------
// Apply selected changes
// -----------------------------------------------------------------------

function applySelected(section) {
  const checks = document.querySelectorAll(`.${section}-check:checked`);
  if (checks.length === 0) {
    showToast('No items selected.', 'warning');
    return;
  }

  const actions = [];
  checks.forEach(cb => {
    try {
      const action = JSON.parse(cb.dataset.action);
      actions.push(action);
    } catch (e) {
      console.error('Bad action JSON:', cb.dataset.action, e);
    }
  });

  if (actions.length === 0) {
    showToast('No valid actions found.', 'warning');
    return;
  }

  // Confirm before applying
  const confirmed = confirm(
    `Apply ${actions.length} change(s) to the new TP files?\n\nA backup will be created automatically.`
  );
  if (!confirmed) return;

  fetch('/apply', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actions }),
  })
  .then(r => r.json())
  .then(d => {
    if (d.success) {
      showToast(d.summary, 'success');
      // Show backup folder location
      if (d.backup_folder) {
        setTimeout(() => showToast(`Backup saved: ${d.backup_folder}`, 'info'), 1200);
        // Also update any on-page backup banner if present
        const banner = document.getElementById('backupBanner');
        const bannerText = document.getElementById('backupBannerText');
        if (banner && bannerText) {
          bannerText.textContent = `Backup saved to: ${d.backup_folder}`;
          banner.style.removeProperty('display');
          banner.style.display = 'flex';
        }
      }
      // Show per-action results
      if (d.results) {
        const failedItems = d.results.filter(r => !r.success);
        if (failedItems.length > 0) {
          const msgs = failedItems.map(r => r.message || 'Unknown error').join('\n');
          setTimeout(() => showToast(`${failedItems.length} action(s) failed:\n${msgs}`, 'danger'), 2500);
        }
      }
      // Reload the compare panel to reflect applied changes
      setTimeout(() => location.reload(), 3800);
    } else {
      showToast('Error: ' + (d.message || 'Unknown error'), 'danger');
    }
  })
  .catch(err => showToast('Network error: ' + err, 'danger'));
}

// -----------------------------------------------------------------------
// MTPL Key Filter
// -----------------------------------------------------------------------

function filterMtplKeys() {
  const rawFilter = (document.getElementById('mtplKeyFilter') || {}).value || '';
  const terms = rawFilter.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  document.querySelectorAll('.mtpl-diff-row').forEach(row => {
    if (terms.length === 0) {
      row.style.display = '';
      return;
    }
    const keyEl = row.querySelector('.mtpl-key-cell');
    const keyText = keyEl ? keyEl.textContent.trim().toLowerCase() : '';
    const visible = terms.some(t => keyText.includes(t));
    row.style.display = visible ? '' : 'none';
  });
}

// -----------------------------------------------------------------------
// Config-page helpers (used inline from config.html)
// -----------------------------------------------------------------------

// `saveConfig` and `validatePaths` are defined inline in config.html
// because they reference form-generated field IDs.
// These helpers are shared utilities.

// Expand/collapse all <details> elements at once
function expandAll() {
  document.querySelectorAll('details').forEach(d => d.open = true);
}
function collapseAll() {
  document.querySelectorAll('details').forEach(d => d.open = false);
}
