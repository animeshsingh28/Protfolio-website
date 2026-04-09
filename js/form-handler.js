document.addEventListener("DOMContentLoaded", () => {
    const contactSection = document.getElementById("contact");
    const contactForm = contactSection?.querySelector("form");
    const submitButton = contactForm?.querySelector("button[type='submit']");
    const statusNode = document.getElementById("contact-form-status");
    const startedAtInput = contactForm?.querySelector("input[name='form_started_at']");

    if (!contactForm || !submitButton || !statusNode || !startedAtInput) {
        return;
    }

    const resetStartTime = () => {
        startedAtInput.value = String(Math.floor(Date.now() / 1000));
    };

    const setStatus = (message, toneClass) => {
        statusNode.textContent = message;
        statusNode.classList.remove("text-secondary", "text-tertiary", "text-error");
        statusNode.classList.add(toneClass);
    };

    resetStartTime();

    contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(contactForm);
        const payload = {
            name: String(formData.get("name") || "").trim(),
            email: String(formData.get("email") || "").trim(),
            subject: String(formData.get("subject") || "").trim(),
            message: String(formData.get("message") || "").trim(),
            company_website: String(formData.get("company_website") || ""),
            form_started_at: String(formData.get("form_started_at") || ""),
        };

        submitButton.disabled = true;
        setStatus("TRANSMITTING...", "text-secondary");

        try {
            const response = await fetch("/api/contact.php", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok && data.success) {
                setStatus("MESSAGE_ACCEPTED", "text-tertiary");
                contactForm.reset();
                resetStartTime();
                if (data.requestId) {
                    console.info("contact request id:", data.requestId);
                }
            } else {
                setStatus(String(data.message || "TRANSMISSION_FAILED").toUpperCase(), "text-error");
            }
        } catch {
            setStatus("NETWORK_ERROR_TRY_AGAIN", "text-error");
        } finally {
            submitButton.disabled = false;
        }
    });
});
