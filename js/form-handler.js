document.addEventListener("DOMContentLoaded", () => {
    const contactSection = document.getElementById("contact");
    const contactForm = contactSection?.querySelector("form");

    if (!contactForm) {
        return;
    }

    contactForm.addEventListener("submit", (event) => {
        event.preventDefault();
        console.info("Contact form submission is not connected to a backend yet.");
    });
});
