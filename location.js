document.addEventListener("DOMContentLoaded", () => {
  // Location elements
  const form = document.getElementById("generate-form");
  const locationInput = document.getElementById("location-input");
  const searchBtn = document.getElementById("search-location");
  const resultsBox = document.getElementById("location-results");
  const status = document.getElementById("status");
  const latInput = document.getElementById("lat");
  const lonInput = document.getElementById("lon");
  const detailsInput = document.getElementById("location_details");
  const card = document.getElementById("location-card");

  let verifiedLocation = false;

  if (!locationInput || !searchBtn) {
    console.error("Location input or Verify button is missing.");
    return;
  }

  // Show status messages
  function showStatus(message, type = "info") {
    if (!status) return;

    status.textContent = message;
    status.classList.remove(
      "d-none",
      "text-danger",
      "text-success",
      "text-muted",
      "text-warning"
    );

    const className = {
      error: "text-danger",
      success: "text-success",
      warning: "text-warning",
      info: "text-muted"
    };

    status.classList.add(className[type] || "text-muted");
  }

  // Update verification badge
  function setBadge(message, type = "warning") {
    const badge = document.getElementById("loc-badge");
    if (!badge) return;

    badge.textContent = message;
    badge.className = "badge " + (
      type === "success"
        ? "bg-success"
        : type === "error"
        ? "bg-danger"
        : "bg-warning text-dark"
    );
  }

  // Update preview card safely
  function setText(id, value) {
    const element = document.getElementById(id);
    if (element) {
      element.textContent = value || "Not available";
    }
  }

  function updatePreview(details) {
    setText("loc-area", details.area);
    setText("loc-city", details.village_town_city);
    setText("loc-mandal", details.mandal_subdistrict);
    setText("loc-district", details.district);
    setText("loc-state", details.state);
    setText("loc-pincode", details.pincode);
    setText("loc-fullname", details.display_name);

    const hasCoordinates =
      details.lat !== "" &&
      details.lon !== "" &&
      Number.isFinite(Number(details.lat)) &&
      Number.isFinite(Number(details.lon));

    setText(
      "loc-coords",
      hasCoordinates
        ? `${Number(details.lat).toFixed(6)}, ${Number(details.lon).toFixed(6)}`
        : "Not verified"
    );

    if (card) card.style.display = "block";
  }

  // When the user edits the location, old verified details
  // must not remain attached to the new location.
  function resetLocationDetails() {
    verifiedLocation = false;

    if (latInput) latInput.value = "";
    if (lonInput) lonInput.value = "";

    if (resultsBox) {
      resultsBox.replaceChildren();
      resultsBox.style.display = "none";
    }

    const query = locationInput.value.trim();
    const parts = query.split(",").map(part => part.trim()).filter(Boolean);

    const details = {
      lat: "",
      lon: "",
      area: "Not available",
      village_town_city: parts[0] || "Not available",
      mandal_subdistrict: "Not available",
      district: "Not available",
      state: parts.length > 1 ? parts[parts.length - 1] : "Not available",
      pincode: "Not available",
      country: "India",
      display_name: query
    };

    if (detailsInput) {
      detailsInput.value = JSON.stringify(details);
    }

    updatePreview(details);
    setBadge("Not verified");

    if (query) {
      showStatus(
        "Location changed. Click Verify / Details to find the correct location.",
        "warning"
      );
    } else if (status) {
      status.textContent = "";
      status.classList.add("d-none");
    }
  }

  // Apply a result returned by the server
  function applyLocation(item) {
    const rawLat = item.lat ?? item.latitude;
    const rawLon = item.lon ?? item.lng ?? item.longitude;

    if (
      rawLat === undefined ||
      rawLat === null ||
      rawLat === "" ||
      rawLon === undefined ||
      rawLon === null ||
      rawLon === ""
    ) {
      showStatus(
        "The search result has no coordinates. Please choose another result.",
        "error"
      );
      return false;
    }

    const lat = Number(rawLat);
    const lon = Number(rawLon);

    if (
      !Number.isFinite(lat) ||
      !Number.isFinite(lon) ||
      lat < -90 || lat > 90 ||
      lon < -180 || lon > 180
    ) {
      showStatus("The location returned invalid coordinates.", "error");
      return false;
    }

    const address = item.address || {};

    const city =
      item.village_town_city ||
      item.city ||
      address.city ||
      address.town ||
      address.village ||
      address.municipality ||
      address.hamlet ||
      "";

    const details = {
      lat: lat,
      lon: lon,
      area:
        item.area ||
        address.suburb ||
        address.neighbourhood ||
        address.residential ||
        "",
      village_town_city: city || item.area || "",
      mandal_subdistrict:
        item.mandal_subdistrict ||
        item.subdistrict ||
        address.city_district ||
        address.subdistrict ||
        "",
      district:
        item.district ||
        address.state_district ||
        address.district ||
        address.county ||
        "",
      state: item.state || address.state || "",
      pincode:
        item.pincode ||
        item.postcode ||
        address.postcode ||
        "",
      country: item.country || address.country || "India",
      display_name: item.display_name || locationInput.value.trim()
    };

    if (!details.village_town_city) {
      details.village_town_city =
        details.display_name.split(",")[0].trim();
    }

    if (latInput) latInput.value = lat.toFixed(6);
    if (lonInput) lonInput.value = lon.toFixed(6);

    if (detailsInput) {
      detailsInput.value = JSON.stringify(details);
    }

    locationInput.value = details.display_name;
    verifiedLocation = true;

    updatePreview(details);
    setBadge("Location Verified", "success");
    showStatus("Location verified successfully.", "success");

    if (resultsBox) {
      resultsBox.replaceChildren();
      resultsBox.style.display = "none";
    }

    return true;
  }

  // Render search results
  function showResults(results) {
    if (!resultsBox) return;

    resultsBox.replaceChildren();

    results.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        "list-group-item list-group-item-action py-2";

      const title = document.createElement("strong");
      title.textContent =
        item.display_name
          ? item.display_name.split(",")[0]
          : "Location result";

      const description = document.createElement("small");
      description.className = "d-block text-muted";
      description.textContent = item.display_name || "";

      button.appendChild(title);
      button.appendChild(description);

      button.addEventListener("click", () => {
        if (applyLocation(item)) {
          resultsBox.style.display = "none";
        }
      });

      resultsBox.appendChild(button);
    });

    resultsBox.style.display = "block";
  }

  // Search for the entered location
  async function searchLocation() {
    const query = locationInput.value.trim();

    if (!query) {
      showStatus("Please enter a location name first.", "error");
      locationInput.focus();
      return;
    }

    searchBtn.disabled = true;
    searchBtn.textContent = "Searching...";

    if (resultsBox) {
      resultsBox.replaceChildren();
      resultsBox.style.display = "none";
    }

    showStatus("Searching for the entered location...", "info");

    try {
      const response = await fetch(
        `/search-location?q=${encodeURIComponent(query)}`,
        {
          method: "GET",
          headers: { "Accept": "application/json" }
        }
      );

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();

      if (!data.ok) {
        throw new Error(data.error || "Location search failed.");
      }

      const results = Array.isArray(data.results)
        ? data.results
        : [];

      if (results.length === 0) {
        verifiedLocation = false;
        setBadge("Not verified", "error");
        showStatus(
          "No matching location found. Check the spelling or try adding the state and country.",
          "error"
        );
        return;
      }

      if (results.length === 1) {
        applyLocation(results[0]);
        return;
      }

      showResults(results);
      showStatus(
        "Select the correct location from the results below.",
        "info"
      );

    } catch (error) {
      console.error("Location search failed:", error);

      verifiedLocation = false;
      setBadge("Search failed", "error");

      showStatus(
        "Location search failed. Check the /search-location server route and try again.",
        "error"
      );

    } finally {
      searchBtn.disabled = false;
      searchBtn.textContent = "🔎 Verify / Details";
    }
  }

  // Events
  locationInput.addEventListener("input", resetLocationDetails);
  searchBtn.addEventListener("click", searchLocation);

  // Prevent submitting an unverified location
  form?.addEventListener("submit", (event) => {
    if (!locationInput.value.trim()) {
      event.preventDefault();
      showStatus("Please enter a business location.", "error");
      locationInput.focus();
      return;
    }

    if (!verifiedLocation) {
      event.preventDefault();
      showStatus(
        "Please click Verify / Details and select a valid search result before generating the blueprint.",
        "error"
      );
      locationInput.focus();
    }
  });

});
