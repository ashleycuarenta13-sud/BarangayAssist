
// Settings page: client-side guard for the change-password form.
// The server re-validates everything, this only saves a wasted round trip.

document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector(".settings-form");

    if (!form) return;

    const current = document.getElementById("currentPassword");
    const next = document.getElementById("newPassword");
    const confirm = document.getElementById("confirmPassword");

    function setError(field, message) {
        if (!field) return;

        field.classList.toggle("is-invalid", Boolean(message));

        let error = field.parentElement.querySelector(".field-error");

        if (message) {
            if (!error) {
                error = document.createElement("small");
                error.className = "field-error";
                field.parentElement.appendChild(error);
            }
            error.textContent = message;
        } else if (error) {
            error.remove();
        }
    }

    // Clear the marker as soon as the user starts correcting a field.
    [current, next, confirm].forEach(function (field) {
        if (!field) return;
        field.addEventListener("input", function () {
            setError(field, "");
        });
    });

    form.addEventListener("submit", function (event) {
        const currentOk = current && current.value.length > 0;
        const nextOk = next && next.value.length >= 8;
        const confirmOk = confirm && confirm.value === next.value &&
            confirm.value.length > 0;

        setError(current, currentOk ? "" : "Enter your current password.");
        setError(
            next,
            nextOk ? "" : "New password must be at least 8 characters."
        );
        setError(
            confirm,
            confirmOk ? "" : "Passwords do not match."
        );

        if (!currentOk || !nextOk || !confirmOk) {
            event.preventDefault();

            const firstInvalid = form.querySelector(".is-invalid");
            if (firstInvalid) firstInvalid.focus();
        }
    });
});
