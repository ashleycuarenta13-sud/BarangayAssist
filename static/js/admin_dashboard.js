document.addEventListener("DOMContentLoaded", function() {


    // =========================================================
    // MOBILE SIDEBAR
    // =========================================================

    const mobileMenu =
        document.getElementById("mobileMenu");

    const sidebar =
        document.getElementById("adminSidebar");


    if (mobileMenu && sidebar) {

        mobileMenu.addEventListener(
            "click",
            function() {

                sidebar.classList.toggle("open");

            }
        );

    }


    // =========================================================
    // CLOSE SIDEBAR WHEN CLICKING OUTSIDE
    // =========================================================

    document.addEventListener(
        "click",
        function(event) {

            if (!sidebar || !mobileMenu) {
                return;
            }


            if (
                sidebar.classList.contains("open") &&
                !sidebar.contains(event.target) &&
                !mobileMenu.contains(event.target)
            ) {

                sidebar.classList.remove("open");

            }

        }
    );


    // =========================================================
    // CONCERN FILTER
    // =========================================================

    const filterButtons =
        document.querySelectorAll(".filter-btn");

    const concernRows =
        document.querySelectorAll(".table-row");


    filterButtons.forEach(
        function(button) {

            button.addEventListener(
                "click",
                function() {


                    // Remove active state
                    filterButtons.forEach(
                        function(btn) {

                            btn.classList.remove("active");

                        }
                    );


                    // Add active state
                    button.classList.add("active");


                    const filter =
                        button.dataset.filter;


                    // Filter rows
                    concernRows.forEach(
                        function(row) {

                            const status =
                                row.dataset.status;


                            if (
                                filter === "all" ||
                                status === filter
                            ) {

                                row.style.display = "";

                            } else {

                                row.style.display = "none";

                            }

                        }
                    );

                }
            );

        }
    );


    // =========================================================
    // MANAGEMENT CARD CLICK EFFECT
    // =========================================================

    const managementButtons =
        document.querySelectorAll(
            ".management-arrow"
        );


    managementButtons.forEach(
        function(button) {

            button.addEventListener(
                "click",
                function() {

                    const card =
                        button.closest(
                            ".management-card"
                        );


                    if (card) {

                        card.style.transform =
                            "translateY(-3px)";


                        setTimeout(
                            function() {

                                card.style.transform =
                                    "";

                            },
                            180
                        );

                    }

                }
            );

        }
    );


});