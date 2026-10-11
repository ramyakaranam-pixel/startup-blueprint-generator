document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('generate-form');
  const ideaInput = document.getElementById('idea-input');

  // Business Category
  const categoryWrapper = document.getElementById('category-wrapper');
  const categoryDisplayInput = document.getElementById('category-display-input');
  const categoryValueInput = document.getElementById('business-category-value');
  const industryValueInput = document.getElementById('industry-value');
  const categoryToggleBtn = document.getElementById('category-toggle-btn');
  const categoryMenu = document.getElementById('category-menu');
  const categoryItems = categoryMenu
    ? categoryMenu.querySelectorAll('.combobox-item')
    : [];

  function filterCategories(query) {
    const q = (query || '').trim().toLowerCase();
    categoryItems.forEach(item => {
      const text = (item.textContent || '').trim().toLowerCase();
      const val = (item.getAttribute('data-value') || '').toLowerCase();
      if (item.parentElement) {
        item.parentElement.style.display =
          !q || text.includes(q) || val.includes(q) ? 'block' : 'none';
      }
    });
  }

  function hideCategoryMenu() {
    if (categoryMenu) categoryMenu.style.display = 'none';
  }

  function showCategoryMenu() {
    if (!categoryMenu) return;
    filterCategories(categoryDisplayInput?.value || '');
    categoryMenu.style.display = 'block';
  }

  categoryDisplayInput?.addEventListener('focus', showCategoryMenu);
  categoryDisplayInput?.addEventListener('click', showCategoryMenu);
  categoryDisplayInput?.addEventListener('input', () => {
    filterCategories(categoryDisplayInput.value);
    if (categoryMenu) categoryMenu.style.display = 'block';
    if (categoryValueInput) categoryValueInput.value = '';
    if (industryValueInput) industryValueInput.value = '';
  });

  categoryToggleBtn?.addEventListener('click', e => {
    e.stopPropagation();
    if (categoryMenu?.style.display === 'block') {
      hideCategoryMenu();
    } else {
      showCategoryMenu();
      categoryDisplayInput?.focus();
    }
  });

  categoryItems.forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      const value = item.getAttribute('data-value') || item.textContent.trim();
      const display = item.getAttribute('data-display') || item.textContent.trim();

      if (categoryDisplayInput) categoryDisplayInput.value = display;
      if (categoryValueInput) categoryValueInput.value = value;
      if (industryValueInput) industryValueInput.value = value;
      hideCategoryMenu();
    });
  });

  // Target Audience
  const audienceWrapper = document.getElementById('audience-wrapper');
  const audienceBtn = document.getElementById('audience-dropdown-btn');
  const audienceBtnLabel = document.getElementById('audience-btn-label');
  const audienceMenu = document.getElementById('audience-menu');
  const audienceSearchInput = document.getElementById('audience-search-input');
  const audienceSelectAllBtn = document.getElementById('audience-select-all-btn');
  const audienceClearAllBtn = document.getElementById('audience-clear-all-btn');
  const audienceCheckboxes = document.querySelectorAll('.audience-checkbox');
  const audienceChipsContainer = document.getElementById('audience-chips-container');

  function hideAudienceMenu() {
    if (audienceMenu) audienceMenu.style.display = 'none';
  }

  function updateAudienceUI() {
    if (!audienceChipsContainer) return;
    audienceChipsContainer.innerHTML = '';
    const selected = Array.from(audienceCheckboxes).filter(cb => cb.checked);

    if (audienceBtnLabel) {
      audienceBtnLabel.textContent = selected.length
        ? `${selected.length} Audience(s) Selected`
        : 'Select Target Audience';
      audienceBtnLabel.className = selected.length
        ? 'text-dark fw-medium'
        : 'text-muted';
    }

    selected.forEach(cb => {
      const chip = document.createElement('span');
      chip.className =
        'badge bg-primary-subtle text-primary border d-inline-flex align-items-center py-2 px-3 rounded-pill gap-2';

      const label = document.createElement('span');
      label.textContent = cb.getAttribute('data-display') || cb.value;

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'btn-close';
      remove.setAttribute('aria-label', 'Remove');
      remove.addEventListener('click', e => {
        e.stopPropagation();
        cb.checked = false;
        updateAudienceUI();
      });

      chip.append(label, remove);
      audienceChipsContainer.appendChild(chip);
    });
  }

  audienceBtn?.addEventListener('click', e => {
    e.stopPropagation();
    if (audienceMenu?.style.display === 'block') {
      hideAudienceMenu();
    } else if (audienceMenu) {
      audienceMenu.style.display = 'block';
      audienceSearchInput?.focus();
    }
  });

  audienceCheckboxes.forEach(cb =>
    cb.addEventListener('change', updateAudienceUI)
  );

  audienceSearchInput?.addEventListener('input', () => {
    const q = audienceSearchInput.value.trim().toLowerCase();
    document.querySelectorAll('.audience-check-item').forEach(item => {
      const label =
        item.querySelector('.form-check-label')?.textContent.toLowerCase() || '';
      item.style.display = !q || label.includes(q) ? 'block' : 'none';
    });
  });

  audienceSelectAllBtn?.addEventListener('click', e => {
    e.stopPropagation();
    document.querySelectorAll('.audience-check-item').forEach(item => {
      if (item.style.display !== 'none') {
        const cb = item.querySelector('.audience-checkbox');
        if (cb) cb.checked = true;
      }
    });
    updateAudienceUI();
  });

  audienceClearAllBtn?.addEventListener('click', e => {
    e.stopPropagation();
    audienceCheckboxes.forEach(cb => { cb.checked = false; });
    updateAudienceUI();
  });

  // Location elements
  const locationInput = document.getElementById('location-input');
  const searchBtn = document.getElementById('search-location');
  const resultsBox = document.getElementById('location-results');
  const status = document.getElementById('status');
  const latInput = document.getElementById('lat');
  const lonInput = document.getElementById('lon');
  const detailsInput = document.getElementById('location_details');
  const card = document.getElementById('location-card');

  let verifiedLocation = false;

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || 'Not available';
  }

  function clearLocation() {
    verifiedLocation = false;

    if (detailsInput) detailsInput.value = '';
    if (latInput) latInput.value = '';
    if (lonInput) lonInput.value = '';
    if (card) card.style.display = 'none';

    [
      'loc-area', 'loc-city', 'loc-mandal', 'loc-district',
      'loc-state', 'loc-pincode', 'loc-coords', 'loc-fullname'
    ].forEach(id => setText(id, 'Not available'));

    if (status) status.textContent = 'Location not verified. Click Verify / Details.';
  }

  function applyLocation(item) {
    const lat = Number(item.lat);
    const lon = Number(item.lon);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
      if (status) status.textContent = 'Invalid coordinates. Please select another result.';
      return;
    }

    const details = {
      lat,
      lon,
      area: item.area || '',
      village_town_city: item.village_town_city || '',
      mandal_subdistrict: item.mandal_subdistrict || '',
      district: item.district || '',
      state: item.state || '',
      pincode: item.pincode || '',
      country: item.country || 'India',
      display_name: item.display_name || ''
    };

    if (latInput) latInput.value = lat.toFixed(6);
    if (lonInput) lonInput.value = lon.toFixed(6);
    if (detailsInput) detailsInput.value = JSON.stringify(details);
    if (locationInput) locationInput.value = details.display_name;

    setText('loc-area', details.area);
    setText('loc-city', details.village_town_city);
    setText('loc-mandal', details.mandal_subdistrict);
    setText('loc-district', details.district);
    setText('loc-state', details.state);
    setText('loc-pincode', details.pincode);
    setText('loc-coords', `${lat.toFixed(6)}, ${lon.toFixed(6)}`);
    setText('loc-fullname', details.display_name);

    if (card) card.style.display = 'block';
    if (resultsBox) {
      resultsBox.innerHTML = '';
      resultsBox.style.display = 'none';
    }

    verifiedLocation = true;
    if (status) status.textContent = 'Location verified successfully.';
  }

  // Typing a new location clears old selected details
  locationInput?.addEventListener('input', () => {
    clearLocation();
    if (resultsBox) {
      resultsBox.innerHTML = '';
      resultsBox.style.display = 'none';
    }
  });

  async function searchLocation() {
    const q = (locationInput?.value || '').trim();

    if (q.length < 2) {
      if (status) status.textContent = 'Enter at least 2 characters.';
      return;
    }

    clearLocation();

    if (searchBtn) {
      searchBtn.disabled = true;
      searchBtn.textContent = 'Searching...';
    }

    if (resultsBox) {
      resultsBox.innerHTML = '';
      resultsBox.style.display = 'none';
    }

    try {
      const response = await fetch(`/search-location?q=${encodeURIComponent(q)}`);
      const data = await response.json();

      if (!response.ok || !data.ok || !Array.isArray(data.results) || !data.results.length) {
        if (status) {
          status.textContent = data.error || 'No location results found. Try another search.';
        }
        return;
      }

      if (!resultsBox) {
        if (status) status.textContent = 'Location results area not found in the page.';
        return;
      }

      data.results.forEach(item => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'list-group-item list-group-item-action py-2';

        const title = document.createElement('strong');
        title.textContent = (item.display_name || q).split(',')[0];

        const description = document.createElement('div');
        description.className = 'small text-muted';
        description.textContent = item.display_name || q;

        btn.append(title, description);
        btn.addEventListener('click', () => applyLocation(item));
        resultsBox.appendChild(btn);
      });

      resultsBox.style.display = 'block';
      if (status) status.textContent = 'Select the correct location from the results.';
    } catch (error) {
      console.error('Location search failed:', error);
      if (status) status.textContent =
        'Search failed. Check internet connection and try again.';
    } finally {
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.textContent = '🔎 Verify / Details';
      }
    }
  }

  searchBtn?.addEventListener('click', searchLocation);

  // Close dropdowns when clicking elsewhere
  document.addEventListener('click', e => {
    if (categoryWrapper && !categoryWrapper.contains(e.target)) hideCategoryMenu();
    if (audienceWrapper && !audienceWrapper.contains(e.target)) hideAudienceMenu();
  });

  // Form validation
  form?.addEventListener('submit', e => {
    const idea = (ideaInput?.value || '').trim();

    if (!idea) {
      e.preventDefault();
      alert('Please enter your Startup Idea.');
      ideaInput?.focus();
      return;
    }

    const category = (categoryValueInput?.value || '').trim();
    if (!category) {
      e.preventDefault();
      alert('Please select a Business Category.');
      categoryDisplayInput?.focus();
      return;
    }

    if (!Array.from(audienceCheckboxes).some(cb => cb.checked)) {
      e.preventDefault();
      alert('Please select at least one Target Audience.');
      if (audienceMenu) audienceMenu.style.display = 'block';
      return;
    }

    if (!(locationInput?.value || '').trim()) {
      e.preventDefault();
      alert('Please enter a Business Location.');
      locationInput?.focus();
      return;
    }

    if (!verifiedLocation || !detailsInput?.value) {
      e.preventDefault();
      alert('Please click Verify / Details and select a location from the results.');
      locationInput?.focus();
    }
  });

  // Do not auto-fill details from typed text on page load.
  // Old location details must be verified again by the user.
  clearLocation();
  updateAudienceUI();
});
