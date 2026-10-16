document.addEventListener("DOMContentLoaded", function() {

    // ASSIGNMENT FORM SUBMISSION
    document.querySelectorAll(".assignment-form").forEach((form) => {
        form.addEventListener("submit", function() {
            const button = form.querySelector(".assign-btn");

            if (!button) return;

            button.disabled = true;
            button.textContent = "Saving...";
            button.setAttribute("aria-busy", "true");
        });
    });

    // =========================================================
    // DARK MODE / LIGHT MODE
    // =========================================================
    const themeButton = document.getElementById("adminDarkModeBtn");
    const themeText = document.getElementById("adminDarkModeText");
    const themeIcon = document.getElementById("adminDarkModeIcon");

    function setTheme(isDark) {
        document.body.classList.toggle("dark-mode", isDark);

        if (themeText) {
            themeText.textContent = isDark ? "Light Mode" : "Dark Mode";
        }

        if (themeIcon) {
            themeIcon.setAttribute(
                "name",
                isDark ? "sunny-outline" : "moon-outline"
            );
        }

        localStorage.setItem("theme", isDark ? "dark" : "light");
    }

    if (localStorage.getItem("theme") === "dark") {
        setTheme(true);
    }

    if (themeButton) {
        themeButton.addEventListener("click", function() {
            setTheme(!document.body.classList.contains("dark-mode"));
        });
    }

    // =========================================================
    // MOBILE SIDEBAR
    // =========================================================
    const mobileMenu = document.getElementById("mobileMenu");
    const sidebar = document.getElementById("adminSidebar");

    if (mobileMenu && sidebar) {
        mobileMenu.addEventListener("click", function() {
            sidebar.classList.toggle("open");
        });
    }

    // Close sidebar when clicking outside
    document.addEventListener("click", function(event) {
        if (!sidebar || !mobileMenu) return;

        if (
            sidebar.classList.contains("open") &&
            !sidebar.contains(event.target) &&
            !mobileMenu.contains(event.target)
        ) {
            sidebar.classList.remove("open");
        }
    });

    // =========================================================
    // CONCERN FILTERING
    // =========================================================
    const filterButtons = document.querySelectorAll(".filter-btn");
    const concernRows = document.querySelectorAll(".table-row");

    filterButtons.forEach(function(button) {
        button.addEventListener("click", function() {

            // Remove active class from other buttons
            filterButtons.forEach(function(btn) {
                btn.classList.remove("active");
            });

            // Activate clicked button
            button.classList.add("active");

            const filter = button.dataset.filter;

            // Filter concern rows
            concernRows.forEach(function(row) {
                const status = row.dataset.status;

                if (filter === "all" || status === filter) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    });

    // =========================================================
    // MANAGEMENT CARD CLICK & NAVIGATION
    // =========================================================
    const managementCards = document.querySelectorAll(".management-card");

    managementCards.forEach(function(card, index) {
        card.style.cursor = "pointer";

        card.addEventListener("click", function() {

            // Visual bounce effect
            card.style.transform = "translateY(-3px)";

            setTimeout(function() {
                card.style.transform = "";
            }, 180);

            // Redirect based on card order
            if (index === 0) {
                window.location.href = "users.php";
            } else if (index === 1) {
                window.location.href = "staff.php";
            } else if (index === 2) {
                window.location.href = "service_routing.php";
            }
        });
    });

    // =========================================================
    // ROW CLICK TO VIEW CONCERN DETAILS
    // =========================================================
    concernRows.forEach(function(row) {
        row.style.cursor = "pointer";

        row.addEventListener("click", function() {
            const concernId = row.dataset.id;

            if (concernId) {
                window.location.href =
                    "view_concern.php?id=" + encodeURIComponent(concernId);
            }
        });
    });

});