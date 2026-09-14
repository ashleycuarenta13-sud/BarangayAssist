function filterConcerns(status) {

    const rows = document.querySelectorAll(".admin-concern-row");

    rows.forEach(row => {

        if (status === "all") {

            row.style.display = "";

        } else {

            const rowStatus = row.dataset.status;

            if (rowStatus === status) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }

        }

    });

}


function searchConcerns() {

    const searchInput =
        document.getElementById("searchConcern");

    const searchText =
        searchInput.value.toLowerCase();

    const rows =
        document.querySelectorAll(".admin-concern-row");


    rows.forEach(row => {

        const text =
            row.textContent.toLowerCase();

        if (text.includes(searchText)) {

            row.style.display = "";

        } else {

            row.style.display = "none";

        }

    });

}