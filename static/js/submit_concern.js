
document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".submit-card form");

    if (!form) return;

    const title = document.getElementById("title");
    const category = document.getElementById("category");
    const description = document.getElementById("description");
    const submitButton = form.querySelector('button[type="submit"]');

    // Preselect a category if the page URL contains ?category=...
    if (category) {
        const params = new URLSearchParams(window.location.search);
        const requestedCategory = params.get("category");

        if (requestedCategory) {
            const matchingOption = Array.from(category.options).find(function (option) {
                return option.value.toLowerCase() === requestedCategory.toLowerCase();
            });

            if (matchingOption) {
                category.value = matchingOption.value;
            }
        }
    }

    const fields = [
        {
            input: title,
            box: document.getElementById("box-title"),
            message: "Please enter a short title for your concern."
        },
        {
            input: description,
            box: document.getElementById("box-description"),
            message: "Please describe the concern before submitting."
        }
    ];

    function clearError(field) {
        if (!field.box) return;

        field.box.classList.remove("is-invalid");

        const error = field.box.querySelector(".field-error");

        if (error) {
            error.remove();
        }
    }

    function showError(field) {
        clearError(field);

        if (!field.box) return;

        field.box.classList.add("is-invalid");

        const error = document.createElement("small");
        error.className = "field-error";
        error.textContent = field.message;

        field.box.appendChild(error);
    }

    // Clear field errors as the user edits.
    fields.forEach(function (field) {
        if (!field.input) return;

        field.input.addEventListener("input", function () {
            if (field.input.value.trim()) {
                clearError(field);
            }
        });

        field.input.addEventListener("change", function () {
            if (field.input.value.trim()) {
                clearError(field);
            }
        });
    });

    // Validate before submitting.
    form.addEventListener("submit", function (event) {
        let valid = true;

        fields.forEach(function (field) {
            if (!field.input || !field.input.value.trim()) {
                showError(field);
                valid = false;
            } else {
                clearError(field);
            }
        });

        if (!category || !category.value) {
            valid = false;
        }

        if (!valid) {
            event.preventDefault();

            const firstInvalid = form.querySelector(
                ".is-invalid input, .is-invalid textarea"
            );

            if (firstInvalid) {
                firstInvalid.focus();
            } else if (category && !category.value) {
                category.focus();
            }

            return;
        }

        // Show the submitting state.
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.setAttribute("aria-busy", "true");
            submitButton.classList.add("is-submitting");
            submitButton.innerHTML =
                '<ion-icon name="sync-outline"></ion-icon> Submitting...';
        }
    });
});
