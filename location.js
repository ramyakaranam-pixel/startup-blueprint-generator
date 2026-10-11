document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const form = document.getElementById('generate-form');
  const ideaInput = document.getElementById('idea-input');
  
  // Business Category Elements
  const categoryWrapper = document.getElementById('category-wrapper');
  const categoryDisplayInput = document.getElementById('category-display-input');
  const categoryValueInput = document.getElementById('business-category-value');
  const industryValueInput = document.getElementById('industry-value');
  const categoryToggleBtn = document.getElementById('category-toggle-btn');
  const categoryMenu = document.getElementById('category-menu');
  const categoryItems = categoryMenu ? categoryMenu.querySelectorAll('.combobox-item') : [];

  // Target Audience Elements
  const audienceWrapper = document.getElementById('audience-wrapper');
  const audienceBtn = document.getElementById('audience-dropdown-btn');
  const audienceBtnLabel = document.getElementById('audience-btn-label');
  const audienceMenu = document.getElementById('audience-menu');
  const audienceSearchInput = document.getElementById('audience-search-input');
  const audienceSelectAllBtn = document.getElementById('audience-select-all-btn');
  const audienceClearAllBtn = document.getElementById('audience-clear-all-btn');
  const audienceCheckboxes = document.querySelectorAll('.audience-checkbox');
  const audienceChipsContainer = document.getElementById('audience-chips-container');

  // Location Elements
  const locationInput = document.getElementById('location-input');
  const searchBtn = document.getElementById('search-location');
  const resultsBox = document.getElementById('location-results');
  const status = document.getElementById('status');
  const latInput = document.getElementById('lat');
  const lonInput = document.getElementById('lon');
  const detailsInput = document.getElementById('location_details');
  const card = document.getElementById('location-card');

  // ==========================================
  // 1. Business Category (Searchable Single Select)
  // ==========================================
  function filterCategories(query) {
    const q = (query || '').trim().toLowerCase();
    categoryItems.forEach(item => {
      const text = (item.textContent || '').trim().toLowerCase();
      const val = (item.getAttribute('data-value') || '').trim().toLowerCase();
      if (!q || text.includes(q) || val.includes(q)) {
        item.parentElement.style.display = 'block';
      } else {
        item.parentElement.style.display = 'none';
      }
    });
  }

  function showCategoryMenu() {
    if (!categoryMenu) return;
    filterCategories(categoryDisplayInput.value);
    categoryMenu.style.display = 'block';
  }

  function hideCategoryMenu() {
    if (categoryMenu) categoryMenu.style.display = 'none';
  }

  categoryDisplayInput?.addEventListener('focus', showCategoryMenu);
  categoryDisplayInput?.addEventListener('click', showCategoryMenu);
  categoryDisplayInput?.addEventListener('input', () => {
    filterCategories(categoryDisplayInput.value);
    if (categoryMenu) categoryMenu.style.display = 'block';
  });

  categoryToggleBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    if (categoryMenu && categoryMenu.style.display === 'block') {
      hideCategoryMenu();
    } else {
      filterCategories('');
      if (categoryMenu) categoryMenu.style.display = 'block';
      categoryDisplayInput?.focus();
    }
  });

  categoryItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const cleanVal = item.getAttribute('data-value') || item.textContent.trim();
      const displayVal = item.getAttribute('data-display') || item.textContent.trim();
      
      if (categoryDisplayInput) categoryDisplayInput.value = displayVal;
      if (categoryValueInput) categoryValueInput.value = cleanVal;
      if (industryValueInput) industryValueInput.value = cleanVal;
      
      hideCategoryMenu();
      categoryDisplayInput?.dispatchEvent(new Event('change', { bubbles: true }));
    });
  });

  document.addEventListener('click', (e) => {
    if (categoryWrapper && !categoryWrapper.contains(e.target)) {
      hideCategoryMenu();
    }
    if (audienceWrapper && !audienceWrapper.contains(e.target)) {
      hideAudienceMenu();
    }
  });

  // ==========================================
  // 2. Target Audience (Multi-Select with Chips)
  // ==========================================
  function updateAudienceUI() {
    if (!audienceChipsContainer) return;
    audienceChipsContainer.innerHTML = '';
    const selectedBoxes = Array.from(audienceCheckboxes).filter(cb => cb.checked);

    if (selectedBoxes.length === 0) {
      if (audienceBtnLabel) {
        audienceBtnLabel.textContent = 'Select Target Audience';
        audienceBtnLabel.className = 'text-muted';
      }
      return;
    }

    if (audienceBtnLabel) {
      audienceBtnLabel.textContent = `${selectedBoxes.length} Audience(s) Selected`;
      audienceBtnLabel.className = 'text-dark fw-medium';
    }

    selectedBoxes.forEach(cb => {
      const display = cb.getAttribute('data-display') || cb.value;
      const chip = document.createElement('span');
      chip.className = 'badge bg-primary-subtle text-primary border border-primary-subtle d-inline-flex align-items-center py-2 px-3 fs-6 rounded-pill gap-2 shadow-sm';
      chip.innerHTML = `<span>${display}</span><button type="button" class="btn-close btn-close-sm" aria-label="Remove" style="font-size: 0.65rem;"></button>`;
      
      chip.querySelector('.btn-close').addEventListener('click', (e) => {
        e.stopPropagation();
        cb.checked = false;
        updateAudienceUI();
      });

      audienceChipsContainer.appendChild(chip);
    });
  }

  function showAudienceMenu() {
    if (audienceMenu) audienceMenu.style.display = 'block';
  }

  function hideAudienceMenu() {
    if (audienceMenu) audienceMenu.style.display = 'none';
  }

  audienceBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    if (audienceMenu && audienceMenu.style.display === 'block') {
      hideAudienceMenu();
    } else {
      showAudienceMenu();
      audienceSearchInput?.focus();
    }
  });

  audienceCheckboxes.forEach(cb => {
    cb.addEventListener('change', updateAudienceUI);
  });

  audienceSearchInput?.addEventListener('input', () => {
    const q = (audienceSearchInput.value || '').trim().toLowerCase();
    const items = document.querySelectorAll('.audience-check-item');
    items.forEach(it => {
      const label = it.querySelector('.form-check-label')?.textContent.toLowerCase() || '';
      if (!q || label.includes(q)) {
        it.style.display = 'block';
      } else {
        it.style.display = 'none';
      }
    });
  });

  audienceSelectAllBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    const visibleItems = document.querySelectorAll('.audience-check-item');
    visibleItems.forEach(it => {
      if (it.style.display !== 'none') {
        const cb = it.querySelector('.audience-checkbox');
        if (cb) cb.checked = true;
      }
    });
    updateAudienceUI();
  });

  audienceClearAllBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    audienceCheckboxes.forEach(cb => { cb.checked = false; });
    updateAudienceUI();
  });

  // ==========================================
  // 3. Location Management (Manual Text Entry, GPS Disabled)
  // ==========================================
  function syncLocationText() {
    const q = (locationInput?.value || '').trim();
    if (!q) return;

    let parts = q.split(',').map(s => s.trim()).filter(Boolean);
    let area = parts[0] || q;
    let district = parts.length > 1 ? parts[1] : area;
    let state = parts.length > 2 ? parts[parts.length - 1] : 'Not available';

    let current = {};
    try {
      current = JSON.parse(detailsInput?.value || '{}');
    } catch (e) {
      current = {};
    }

    const safeDetails = {
      lat: current.lat || '',
      lon: current.lon || '',
      area: current.area || area,
      village_town_city: current.village_town_city || area,
      mandal_subdistrict: current.mandal_subdistrict || 'Not available',
      district: current.district || district,
      state: current.state || state,
      pincode: current.pincode || 'Not available',
      country: current.country || 'India',
      display_name: q
    };

    if (detailsInput) detailsInput.value = JSON.stringify(safeDetails);

    const areaElem = document.getElementById('loc-area');
    if (areaElem) areaElem.textContent = safeDetails.area || 'Not available';
    const cityElem = document.getElementById('loc-city');
    if (cityElem) cityElem.textContent = safeDetails.village_town_city || 'Not available';
    const mandalElem = document.getElementById('loc-mandal');
    if (mandalElem) mandalElem.textContent = safeDetails.mandal_subdistrict || 'Not available';
    const distElem = document.getElementById('loc-district');
    if (distElem) distElem.textContent = safeDetails.district || 'Not available';
    const stateElem = document.getElementById('loc-state');
    if (stateElem) stateElem.textContent = safeDetails.state || 'Not available';
    const pinElem = document.getElementById('loc-pincode');
    if (pinElem) pinElem.textContent = safeDetails.pincode || 'Not available';
    const coordsElem = document.getElementById('loc-coords');
    if (coordsElem) {
      coordsElem.textContent = (safeDetails.lat && safeDetails.lon) ? `${safeDetails.lat}, ${safeDetails.lon}` : 'Manual text entry';
    }
    const fullElem = document.getElementById('loc-fullname');
    if (fullElem) fullElem.textContent = q;
  }

  locationInput?.addEventListener('input', syncLocationText);

  function applyLocation(lat, lon, d, message = '✅ Location confirmed.') {
    const latNum = Number(lat);
    const lonNum = Number(lon);
    if (latInput) latInput.value = isNaN(latNum) ? '' : latNum.toFixed(6);
    if (lonInput) lonInput.value = isNaN(lonNum) ? '' : lonNum.toFixed(6);

    const safeDetails = {
      lat: isNaN(latNum) ? '' : latNum,
      lon: isNaN(lonNum) ? '' : lonNum,
      area: (d?.area || '').trim() || 'Not available',
      village_town_city: (d?.village_town_city || '').trim() || (d?.area || '').trim() || 'Not available',
      mandal_subdistrict: (d?.mandal_subdistrict || '').trim() || 'Not available',
      district: (d?.district || '').trim() || 'Not available',
      state: (d?.state || '').trim() || 'Not available',
      pincode: (d?.pincode || '').trim() || 'Not available',
      country: (d?.country || 'India').trim(),
      display_name: (d?.display_name || '').trim()
    };

    if (detailsInput) detailsInput.value = JSON.stringify(safeDetails);
    if (locationInput) locationInput.value = safeDetails.display_name;

    const areaElem = document.getElementById('loc-area');
    if (areaElem) areaElem.textContent = safeDetails.area;
    const cityElem = document.getElementById('loc-city');
    if (cityElem) cityElem.textContent = safeDetails.village_town_city;
    const mandalElem = document.getElementById('loc-mandal');
    if (mandalElem) mandalElem.textContent = safeDetails.mandal_subdistrict;
    const distElem = document.getElementById('loc-district');
    if (distElem) distElem.textContent = safeDetails.district;
    const stateElem = document.getElementById('loc-state');
    if (stateElem) stateElem.textContent = safeDetails.state;
    const pinElem = document.getElementById('loc-pincode');
    if (pinElem) pinElem.textContent = safeDetails.pincode;
    const coordsElem = document.getElementById('loc-coords');
    if (coordsElem) {
      coordsElem.textContent = (!isNaN(latNum) && !isNaN(lonNum) && latNum !== 0) ? `${latNum.toFixed(6)}, ${lonNum.toFixed(6)}` : 'Not available';
    }
    const fullElem = document.getElementById('loc-fullname');
    if (fullElem) fullElem.textContent = safeDetails.display_name;

    if (card) card.style.display = 'block';
  }

  async function searchLocation() {
    const q = (locationInput?.value || '').trim();
    if (!q) {
      alert('Please enter a location name (e.g. Visakhapatnam, Bengaluru, Hyderabad).');
      return;
    }
    if (searchBtn) {
      searchBtn.disabled = true;
      searchBtn.textContent = '🔎 Searching...';
    }
    if (resultsBox) {
      resultsBox.innerHTML = '';
      resultsBox.style.display = 'none';
    }

    try {
      const r = await fetch(`/search-location?q=${encodeURIComponent(q)}`);
      const data = await r.json();
      if (!data.ok || !data.results?.length) {
        const fallbackBtn = document.createElement('button');
        fallbackBtn.type = 'button';
        fallbackBtn.className = 'list-group-item list-group-item-action py-2 list-group-item-light';
        fallbackBtn.innerHTML = `<strong>Use "${q}" as location</strong>`;
        fallbackBtn.addEventListener('click', () => {
          applyLocation('', '', {
            area: q,
            village_town_city: q,
            district: '',
            state: '',
            pincode: '',
            country: 'India',
            display_name: q
          });
          if (resultsBox) resultsBox.style.display = 'none';
        });
        if (resultsBox) {
          resultsBox.appendChild(fallbackBtn);
          resultsBox.style.display = 'block';
        }
        syncLocationText();
        return;
      }

      if (resultsBox) {
        data.results.forEach(item => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'list-group-item list-group-item-action py-2';
          btn.innerHTML = `<strong>${item.display_name.split(',')[0]}</strong><br><small class="text-muted">${item.display_name}</small>`;
          btn.addEventListener('click', () => {
            applyLocation(item.lat, item.lon, item);
            resultsBox.style.display = 'none';
          });
          resultsBox.appendChild(btn);
        });
        resultsBox.style.display = 'block';
      }
    } catch (e) {
      syncLocationText();
    } finally {
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.textContent = '🔎 Verify / Details';
      }
    }
  }

  searchBtn?.addEventListener('click', searchLocation);

  // ==========================================
  // 4. Form Submission Validation
  // ==========================================
  form?.addEventListener('submit', (e) => {
    const idea = (ideaInput?.value || '').trim();
    if (!idea) {
      e.preventDefault();
      alert('Please enter your Startup Idea.');
      ideaInput?.focus();
      return false;
    }

    const catVal = (categoryValueInput?.value || categoryDisplayInput?.value || '').trim();
    if (!catVal) {
      e.preventDefault();
      alert('Please select a Business Category.');
      categoryDisplayInput?.focus();
      return false;
    }

    const selectedAudiences = Array.from(audienceCheckboxes).filter(cb => cb.checked);
    if (selectedAudiences.length === 0) {
      e.preventDefault();
      alert('Please select at least one Target Audience.');
      if (audienceMenu) audienceMenu.style.display = 'block';
      return false;
    }

    const loc = (locationInput?.value || '').trim();
    if (!loc) {
      e.preventDefault();
      alert('Please enter a Business Location.');
      locationInput?.focus();
      return false;
    }

    syncLocationText();
    return true;
  });

  // Initial sync
  syncLocationText();
});
