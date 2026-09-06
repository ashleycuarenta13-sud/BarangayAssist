/* =====================================================
   BARANGAYASSIST DASHBOARD JAVASCRIPT
   ===================================================== */


/* =====================================================
   MOBILE SIDEBAR
   ===================================================== */

const mobileMenu = document.getElementById("mobileMenu");
const sidebar = document.getElementById("sidebar");

if (mobileMenu && sidebar) {

    mobileMenu.addEventListener("click", function() {

        sidebar.classList.toggle("open");

    });

}


/* =====================================================
   DARK / LIGHT MODE
   ===================================================== */

const themeToggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");
const themeText = document.getElementById("themeText");


/* Check saved theme */

const savedTheme = localStorage.getItem("barangayAssistTheme");

if (savedTheme === "dark") {

    document.body.classList.add("dark-mode");

    if (themeIcon) {
        themeIcon.setAttribute("name", "sunny-outline");
    }

    if (themeText) {
        themeText.textContent = "Light Mode";
    }

}


/* Toggle theme */

if (themeToggle) {

    themeToggle.addEventListener("click", function() {

        document.body.classList.toggle("dark-mode");

        const isDark =
            document.body.classList.contains("dark-mode");


        if (isDark) {

            localStorage.setItem(
                "barangayAssistTheme",
                "dark"
            );

            if (themeIcon) {
                themeIcon.setAttribute(
                    "name",
                    "sunny-outline"
                );
            }

            if (themeText) {
                themeText.textContent = "Light Mode";
            }

        } else {

            localStorage.setItem(
                "barangayAssistTheme",
                "light"
            );

            if (themeIcon) {
                themeIcon.setAttribute(
                    "name",
                    "moon-outline"
                );
            }

            if (themeText) {
                themeText.textContent = "Dark Mode";
            }

        }

    });

}


/* =====================================================
   FILE A CONCERN BUTTON
   ===================================================== */

const fileConcernBtn =
    document.getElementById("fileConcernBtn");

if (fileConcernBtn) {

    fileConcernBtn.addEventListener("click", function() {

        alert(
            "Concern Submission\n\n" +
            "This will open the concern submission form."
        );

        /*
        Later, if you already have a submission page,
        you can use:

        window.location.href = "pages/submit-concern.html";
        */

    });

}


/* =====================================================
   SIDEBAR SUBMIT CONCERN
   ===================================================== */

const submitConcern =
    document.getElementById("submitConcern");

if (submitConcern) {

    submitConcern.addEventListener("click", function(e) {

        e.preventDefault();

        alert(
            "Concern Submission\n\n" +
            "This will open the concern submission form."
        );

    });

}


/* =====================================================
   COMMON CONCERN BUTTONS
   ===================================================== */

const concernTypes =
    document.querySelectorAll(".concern-type");


concernTypes.forEach(function(button) {

    button.addEventListener("click", function() {

        const concernName =
            button.querySelector("small").textContent;

        alert(
            "Selected Concern:\n\n" +
            concernName +
            "\n\n" +
            "You can use this category when submitting your concern."
        );

    });

});


/* =====================================================
   CLOSE SIDEBAR AFTER CLICK
   ===================================================== */

const navItems =
    document.querySelectorAll(".nav-item");


navItems.forEach(function(item) {

    item.addEventListener("click", function() {

        if (window.innerWidth <= 800) {

            sidebar.classList.remove("open");

        }

    });

});


/* =====================================================
   CLOSE SIDEBAR WHEN CLICKING OUTSIDE
   ===================================================== */

document.addEventListener("click", function(event) {

    if (window.innerWidth > 800) {
        return;
    }

    if (!sidebar || !mobileMenu) {
        return;
    }

    const clickedInsideSidebar =
        sidebar.contains(event.target);

    const clickedMenu =
        mobileMenu.contains(event.target);

    if (!clickedInsideSidebar && !clickedMenu) {

        sidebar.classList.remove("open");

    }

});