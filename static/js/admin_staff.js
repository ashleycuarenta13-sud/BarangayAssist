
// Staff page: live search over the staff workload table.

document.addEventListener("DOMContentLoaded", function () {
    const search = document.getElementById("searchStaff");

    if (!search) return;

    const rows = Array.from(document.querySelectorAll(".admin-staff-row"));
    const noResults = document.getElementById("noStaffResults");

    function filterRows() {
        const query = search.value.trim().toLowerCase();
        let visible = 0;

        rows.forEach(function (row) {
            const haystack = row.dataset.search || row.textContent.toLowerCase();
            const matches = haystack.includes(query);

            row.style.display = matches ? "" : "none";
            if (matches) visible++;
        });

        if (noResults) {
            noResults.hidden = !(visible === 0 && rows.length > 0);
        }
    }

    search.addEventListener("input", filterRows);
});
