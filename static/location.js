document.addEventListener("DOMContentLoaded", function () {
    const locationInput = document.getElementById("location");
    const locationDetailsInput =
        document.getElementById("location_details");

    if (!locationInput) {
        console.error("Location input field not found.");
        return;
    }

    let resultBox = document.getElementById("location-results");

    if (!resultBox) {
        resultBox = document.createElement("div");
        resultBox.id = "location-results";

        resultBox.style.border = "1px solid #ddd";
        resultBox.style.borderRadius = "8px";
        resultBox.style.background = "#fff";
        resultBox.style.color = "#222";
        resultBox.style.maxHeight = "240px";
        resultBox.style.overflowY = "auto";
        resultBox.style.display = "none";
        resultBox.style.position = "relative";
        resultBox.style.zIndex = "1000";

        locationInput.insertAdjacentElement("afterend", resultBox);
    }

    let timer = null;
    let controller = null;

    function showMessage(message) {
        resultBox.innerHTML = "";
        const item = document.createElement("div");
        item.textContent = message;
        item.style.padding = "12px";
        resultBox.appendChild(item);
        resultBox.style.display = "block";
    }

    function saveLocation(item) {
        const address = item.address || {};

        const details = {
            lat: Number(item.lat),
            lon: Number(item.lon),
            display_name: item.display_name || "",
            area:
                address.suburb ||
                address.neighbourhood ||
                address.quarter ||
                address.residential ||
                address.village ||
                address.town ||
                address.city ||
                address.hamlet ||
                "",
            village_town_city:
                address.city ||
                address.town ||
                address.village ||
                address.municipality ||
                address.hamlet ||
                "",
            mandal_subdistrict:
                address.subdistrict ||
                address.mandal ||
                address.tehsil ||
                address.county ||
                "",
            district:
                address.state_district ||
                address.district ||
                address.city_district ||
                "",
            state: address.state || "",
            pincode: address.postcode || "",
            country: address.country || ""
        };

        locationInput.value = details.display_name;

        if (locationDetailsInput) {
            locationDetailsInput.value = JSON.stringify(details);
        }

        locationInput.dataset.locationSelected = "true";

        resultBox.style.display = "none";
        resultBox.innerHTML = "";

        locationInput.dispatchEvent(
            new Event("change", { bubbles: true })
        );
    }

    async function searchLocation(query) {
        if (controller) {
            controller.abort();
        }

        controller = new AbortController();

        showMessage("Searching locations...");

        try {
            const response = await fetch(
                "/search-location?q=" +
                encodeURIComponent(query),
                { signal: controller.signal }
            );

            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(
                    data.error || "Unable to search locations."
                );
            }

            resultBox.innerHTML = "";

            if (!data.results || data.results.length === 0) {
                showMessage(
                    "No locations found. Try another spelling."
                );
                return;
            }

            data.results.forEach(function (item) {
                const option = document.createElement("button");

                option.type = "button";
                option.textContent = item.display_name;
                option.style.display = "block";
                option.style.width = "100%";
                option.style.padding = "12px";
                option.style.border = "0";
                option.style.borderBottom = "1px solid #eee";
                option.style.background = "#fff";
                option.style.color = "#222";
                option.style.textAlign = "left";
                option.style.cursor = "pointer";

                option.addEventListener("click", function () {
                    saveLocation(item);
                });

                resultBox.appendChild(option);
            });

            resultBox.style.display = "block";
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }

            console.error("Location search error:", error);
            showMessage(
                "Location search failed. Check your internet and try again."
            );
        }
    }

    locationInput.addEventListener("input", function () {
        clearTimeout(timer);
        locationInput.dataset.locationSelected = "false";

        if (locationDetailsInput) {
            locationDetailsInput.value = "";
        }

        const query = locationInput.value.trim();

        if (query.length < 2) {
            resultBox.style.display = "none";
            resultBox.innerHTML = "";
            return;
        }

        timer = setTimeout(function () {
            searchLocation(query);
        }, 500);
    });

    locationInput.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            resultBox.style.display = "none";
        }
    });

    document.addEventListener("click", function (event) {
        if (
            event.target !== locationInput &&
            !resultBox.contains(event.target)
        ) {
            resultBox.style.display = "none";
        }
    });

    const form = locationInput.closest("form");

    if (form) {
        form.addEventListener("submit", function (event) {
            if (
                locationInput.value.trim() &&
                locationInput.dataset.locationSelected !== "true"
            ) {
                event.preventDefault();
                alert(
                    "Please select a location from the search results."
                );
                locationInput.focus();
            }
        });
    }
});
