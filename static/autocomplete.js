(function () {
  const SUGGESTIONS = window.FAI_SUGGESTIONS;

  const sheetSelect = document.getElementById('sheet-select');
  const vendorInput = document.getElementById('vendor-input');
  const vendorList  = document.getElementById('vendor-list');
  const pnInput     = document.getElementById('pn-input');
  const pnList      = document.getElementById('pn-list');

  function currentSuggestions() {
    return SUGGESTIONS[sheetSelect.value] || { vendors: [], pns: [], vendor_pns: {} };
  }

  function getVendorPns(sugg, vendorValue) {
    const v = vendorValue.trim().toLowerCase();
    if (!v) return null;
    const vendorPns = sugg.vendor_pns || {};
    for (const key of Object.keys(vendorPns)) {
      if (key.toLowerCase() === v) return vendorPns[key];
    }
    return null;
  }

  function closeList(list) {
    list.classList.remove('open');
    list.innerHTML = '';
  }

  function buildDropdown(input, list, items) {
    const q = input.value.trim().toLowerCase();
    list.innerHTML = '';

    if (!q) { list.classList.remove('open'); return; }

    const matches = items.filter(function (s) {
      return s.toLowerCase().includes(q);
    }).slice(0, 12);

    if (matches.length === 0) { list.classList.remove('open'); return; }

    matches.forEach(function (text) {
      const li = document.createElement('li');
      li.textContent = text;
      li.addEventListener('mousedown', function (e) {
        e.preventDefault();
        input.value = text;
        closeList(list);
      });
      list.appendChild(li);
    });

    list.classList.add('open');
  }

  function navigate(list, dir) {
    const items = list.querySelectorAll('li');
    if (!items.length) return;
    let idx = -1;
    items.forEach(function (li, i) {
      if (li.classList.contains('active')) { li.classList.remove('active'); idx = i; }
    });
    idx += dir;
    if (idx < 0) idx = items.length - 1;
    if (idx >= items.length) idx = 0;
    items[idx].classList.add('active');
    items[idx].scrollIntoView({ block: 'nearest' });
  }

  function attachAutocomplete(input, list, getItems) {
    input.addEventListener('input', function () {
      buildDropdown(input, list, getItems());
    });

    input.addEventListener('keydown', function (e) {
      if (!list.classList.contains('open')) return;

      if (e.key === 'ArrowDown') { e.preventDefault(); navigate(list, 1); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); navigate(list, -1); return; }
      if (e.key === 'Escape')    { closeList(list); return; }

      if (e.key === 'Tab') {
        const target = list.querySelector('li.active') || list.querySelector('li');
        if (target) {
          input.value = target.textContent;
          closeList(list);
        }
        return;
      }

      if (e.key === 'Enter') {
        const active = list.querySelector('li.active');
        if (active) {
          e.preventDefault();
          input.value = active.textContent;
          closeList(list);
        }
        // no active item → fall through, form submits normally
      }
    });

    document.addEventListener('click', function (e) {
      if (!input.contains(e.target) && !list.contains(e.target)) {
        closeList(list);
      }
    });
  }

  attachAutocomplete(vendorInput, vendorList, function () {
    return currentSuggestions().vendors;
  });

  attachAutocomplete(pnInput, pnList, function () {
    const sugg = currentSuggestions();
    const filtered = getVendorPns(sugg, vendorInput.value);
    return filtered !== null ? filtered : sugg.pns;
  });

  sheetSelect.addEventListener('change', function () {
    vendorInput.value = '';
    pnInput.value = '';
    closeList(vendorList);
    closeList(pnList);
  });
})();

// Initialize Bootstrap tooltips
document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
  new bootstrap.Tooltip(el, { trigger: 'hover' });
});

// Toggle "View / Hide Raw Records" button label
var rawRecordsEl = document.getElementById('rawRecords');
if (rawRecordsEl) {
  var rawBtn = document.querySelector('[data-bs-target="#rawRecords"]');
  if (rawBtn) {
    rawRecordsEl.addEventListener('show.bs.collapse', function () {
      rawBtn.textContent = rawBtn.textContent.trim().replace('View Raw Records', 'Hide Raw Records');
    });
    rawRecordsEl.addEventListener('hide.bs.collapse', function () {
      rawBtn.textContent = rawBtn.textContent.trim().replace('Hide Raw Records', 'View Raw Records');
    });
  }
}

// Secret debug panel — click the version badge to toggle
var versionBadge = document.getElementById('version-badge');
var debugPanel = document.getElementById('debug-panel');
if (versionBadge && debugPanel) {
  versionBadge.addEventListener('click', function () {
    debugPanel.style.display = debugPanel.style.display === 'none' ? 'block' : 'none';
  });
}
