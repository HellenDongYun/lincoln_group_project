(() => {
    'use strict'

    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(alert => {
        const timeoutId = setTimeout(() => {
            alert.classList.remove("show");
            alert.addEventListener("transitionend", () => alert.remove(), { once: true });
            clearTimeout(timeoutId);
        }, 5000);
    });
})()