
document.addEventListener("DOMContentLoaded", function () {
    const dashboard = document.querySelector(".admin-dashboard");
    const themeButton = document.getElementById("adminDarkModeBtn");
    const themeText = document.getElementById("adminDarkModeText");
    const themeIcon = document.getElementById("adminDarkModeIcon");
    const mobileMenu = document.getElementById("mobileMenu");
    const sidebar = document.getElementById("adminSidebar");

    // DARK MODE
    // The CSS has TWO dark-mode selector systems: `body.dark-mode ...`
    // (admin_dashboard.css final section + admin_pages.css) and
    // `.admin-dashboard.dark-mode ...`. Toggle BOTH so every rule fires.
    function setTheme(isDark) {
        document.body.classList.toggle("dark-mode", isDark);

        if (dashboard) {
            dashboard.classList.toggle("dark-mode", isDark);
        }

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

    setTheme(localStorage.getItem("theme") === "dark");

    if (themeButton) {
        themeButton.addEventListener("click", function (event) {
            event.stopPropagation();
            setTheme(!document.body.classList.contains("dark-mode"));
        });
    }

    // MOBILE SIDEBAR
    if (mobileMenu && sidebar) {
        mobileMenu.addEventListener("click", function (event) {
            event.stopPropagation();
            sidebar.classList.toggle("open");
        });

        document.addEventListener("click", function (event) {
            if (
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !mobileMenu.contains(event.target)
            ) {
                sidebar.classList.remove("open");
            }
        });

        sidebar.querySelectorAll("a.admin-nav-link").forEach(function (link) {
            link.addEventListener("click", function () {
                sidebar.classList.remove("open");
            });
        });
    }

    // ASSIGNMENT FORMS
    document.querySelectorAll(".assignment-form").forEach(function (form) {
        form.addEventListener("submit", function () {
            const button = form.querySelector(".assign-btn");

            if (!button) return;

            button.disabled = true;
            button.textContent = "Saving...";
            button.setAttribute("aria-busy", "true");
        });
    });

    // FILTER CONCERNS
    const filterButtons = document.querySelectorAll(".filter-btn");

    function normalizeStatus(value) {
        return (value || "").trim().toLowerCase().replace(/\s+/g, " ");
    }

    function filterConcerns(status) {
        const filter = normalizeStatus(status);
        const rows = document.querySelectorAll(".table-row, .admin-concern-row");

        rows.forEach(function (row) {
            const rowStatus = normalizeStatus(row.dataset.status);
            const matches = filter === "all" || rowStatus === filter;
            row.style.display = matches ? "" : "none";
        });

        filterButtons.forEach(function (button) {
            button.classList.toggle(
                "active",
                normalizeStatus(button.dataset.filter || "all") === filter
            );
        });
    }

    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            filterConcerns(button.dataset.filter || "all");
        });
    });

    // SEARCH CONCERNS
    const noResults = document.getElementById("noSearchResults");

    function rowMatchesFilters(row) {
        const searchInput = document.getElementById("searchConcern");
        const searchText = searchInput
            ? searchInput.value.trim().toLowerCase()
            : "";
        const rowText = row.textContent.toLowerCase();
        const activeFilter = document.querySelector(".filter-btn.active");
        const filter = normalizeStatus(
            activeFilter ? activeFilter.dataset.filter : "all"
        );
        const rowStatus = normalizeStatus(row.dataset.status);
        const matchesFilter = filter === "all" || rowStatus === filter;

        return {
            matches: rowText.includes(searchText) && matchesFilter,
            hasSearch: searchText.length > 0
        };
    }

    function searchConcerns() {
        const rows = document.querySelectorAll(".table-row, .admin-concern-row");
        let visible = 0;
        let hasSearch = false;

        rows.forEach(function (row) {
            const result = rowMatchesFilters(row);
            row.style.display = result.matches ? "" : "none";

            if (result.hasSearch) hasSearch = true;
            if (result.matches) visible++;
        });

        // Only surface the empty state when a search/filter is active,
        // so the real "no data yet" empty state is not doubled up.
        if (noResults) {
            noResults.hidden = !(hasSearch && visible === 0);
        }
    }

    const searchInput = document.getElementById("searchConcern");

    if (searchInput) {
        searchInput.addEventListener("input", searchConcerns);
    }

    // Re-run the search when a filter button is clicked so both stay in sync.
    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            if (searchInput) searchConcerns();
        });
    });

    // Allow existing HTML onclick attributes to call these functions.
    window.filterConcerns = filterConcerns;
    window.searchConcerns = searchConcerns;

    // MANAGEMENT CARDS
    document.querySelectorAll(".management-card").forEach(function (card) {
        const link = card.querySelector("a[href]");
        const targetUrl = card.dataset.url || (link ? link.href : "");

        if (!targetUrl) return;

        card.style.cursor = "pointer";
        card.setAttribute("tabindex", "0");
        card.setAttribute("role", "link");

        function openManagementPage() {
            window.location.href = targetUrl;
        }

        card.addEventListener("click", function (event) {
            if (event.target.closest("button, a, select, form, input")) return;
            openManagementPage();
        });

        card.addEventListener("keydown", function (event) {
            if (
                (event.key === "Enter" || event.key === " ") &&
                event.target === card
            ) {
                event.preventDefault();
                openManagementPage();
            }
        });
    });

    // CLICKABLE CONCERN ROWS
    document.querySelectorAll(".table-row, .admin-concern-row").forEach(function (row) {
        const targetUrl = row.dataset.url;

        if (!targetUrl) return;

        row.style.cursor = "pointer";
        row.setAttribute("tabindex", "0");

        row.addEventListener("click", function (event) {
            if (event.target.closest("button, a, select, form, input, textarea")) return;
            window.location.href = targetUrl;
        });

        row.addEventListener("keydown", function (event) {
            if (
                (event.key === "Enter" || event.key === " ") &&
                event.target === row
            ) {
                event.preventDefault();
                window.location.href = targetUrl;
            }
        });
    });
});
