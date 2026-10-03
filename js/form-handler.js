document.addEventListener("DOMContentLoaded", () => {
    const contactSection = document.getElementById("contact");
    const contactForm = contactSection?.querySelector("form");
    const submitButton = contactForm?.querySelector("button[type='submit']");
    const statusNode = document.getElementById("contact-form-status");
    const startedAtInput = contactForm?.querySelector("input[name='form_started_at']");

    if (!contactForm || !submitButton || !statusNode || !startedAtInput) {
        return;
    }

    const REQUEST_TIMEOUT_MS = 25000;
    const FALLBACK_ERROR = "Transmission failed. Please try again or email me directly.";

    // The API returns either readable text or a machine code; map the codes.
    // Keep messages in sentence case: the status line is upper-cased by CSS,
    // and screen readers read the underlying text.
    const ERROR_MESSAGES = {
        blocked_fill_time: "Please wait a few seconds, then send again. If this keeps happening, email me directly.",
        blocked_honeypot: "Message could not be sent. Please email me directly.",
    };

    const requiredFields = Array.from(contactForm.querySelectorAll("[required]"));

    const resetStartTime = () => {
        startedAtInput.value = String(Math.floor(Date.now() / 1000));
    };

    const setStatus = (message, toneClass) => {
        statusNode.textContent = message;
        statusNode.classList.remove("text-secondary", "text-tertiary", "text-error");
        statusNode.classList.add(toneClass);
    };

    const describeError = (message) => {
        const text = String(message || "");
        return ERROR_MESSAGES[text] || text || FALLBACK_ERROR;
    };

    const isFieldValid = (field) => field.value.trim() !== "" && field.validity.valid;

    const validateFields = () => {
        const invalidFields = requiredFields.filter((field) => !isFieldValid(field));
        requiredFields.forEach((field) => {
            if (invalidFields.includes(field)) {
                field.setAttribute("aria-invalid", "true");
            } else {
                field.removeAttribute("aria-invalid");
            }
        });
        return invalidFields;
    };

    resetStartTime();

    contactForm.addEventListener("input", (event) => {
        event.target.removeAttribute?.("aria-invalid");
    });

    contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const invalidFields = validateFields();
        if (invalidFields.length > 0) {
            setStatus("Please fill in every field with a valid email address.", "text-error");
            invalidFields[0].focus();
            return;
        }

        const formData = new FormData(contactForm);
        const payload = {
            name: String(formData.get("name") || "").trim(),
            email: String(formData.get("email") || "").trim(),
            subject: String(formData.get("subject") || "").trim(),
            message: String(formData.get("message") || "").trim(),
            company_website: String(formData.get("company_website") || ""),
            form_started_at: String(formData.get("form_started_at") || ""),
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        submitButton.disabled = true;
        contactForm.setAttribute("aria-busy", "true");
        setStatus("TRANSMITTING...", "text-secondary");

        try {
            const response = await fetch("/api/contact.php", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
                signal: controller.signal,
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
                setStatus(describeError(data.message), "text-error");
            }
        } catch (error) {
            const timedOut = error?.name === "AbortError";
            setStatus(timedOut ? "Request timed out. Please try again." : "Network error. Please try again.", "text-error");
        } finally {
            clearTimeout(timeoutId);
            submitButton.disabled = false;
            contactForm.removeAttribute("aria-busy");
        }
    });
});
