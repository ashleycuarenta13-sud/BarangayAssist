document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('.staff-dashboard-page');

    if (!page) return;

    const statusForms = page.querySelectorAll('.admin-controls form');

    statusForms.forEach((form) => {
        const select = form.querySelector('select[name="status"]');
        const button = form.querySelector('button[type="submit"]');
        const row = form.closest('.admin-concern-row');

        if (select) {
            select.addEventListener('change', () => {
                if (row) {
                    row.classList.add('status-being-edited');

                    window.setTimeout(() => {
                        row.classList.remove('status-being-edited');
                    }, 700);
                }
            });
        }

        form.addEventListener('submit', () => {
            if (!button) return;

            button.disabled = true;
            button.setAttribute('aria-busy', 'true');
            button.textContent = 'Updating...';

            if (row) {
                row.classList.add('status-updating');
            }
        });
    });
});