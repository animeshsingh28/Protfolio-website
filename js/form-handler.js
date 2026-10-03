document.addEventListener("DOMContentLoaded", () => {
    const contactSection = document.getElementById("contact");
    const contactForm = contactSection?.querySelector("form");
    const submitButton = contactForm?.querySelector("button[type='submit']");
    const statusNode = document.getElementById("contact-form-status");
    const startedAtInput = contactForm?.querySelector("input[name='form_started_at']");

    if (!contactForm || !submitButton || !statusNode || !startedAtInput) {
        return;
    }

    // Generous, because the server saves the message before sending the email
    // and mail() can block for a long time. This is not a hard bound on server
    // time (PHP's max_execution_time excludes time blocked in I/O), so a
    // timeout is reported as "may have been sent" rather than as a failure.
    const REQUEST_TIMEOUT_MS = 45000;
    const FALLBACK_ERROR = "Transmission failed. Please try again or email me directly.";
    const UNCERTAIN_ERROR = "No reply from the server. Your message may have been sent, so please check with me before resending.";

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

    const validateFields = () => requiredFields.filter((field) => {
        const invalid = !isFieldValid(field);
        if (invalid) {
            field.setAttribute("aria-invalid", "true");
        } else {
            field.removeAttribute("aria-invalid");
        }
        return invalid;
    });

    let showingValidationError = false;

    const markReceived = (requestId) => {
        setStatus("MESSAGE_ACCEPTED", "text-tertiary");
        contactForm.reset();
        resetStartTime();
        if (requestId) {
            console.info("contact request id:", requestId);
        }
    };

    resetStartTime();

    contactForm.addEventListener("input", (event) => {
        event.target.removeAttribute?.("aria-invalid");
        // Clear the error line only once every required field is actually valid,
        // not merely edited.
        if (showingValidationError && requiredFields.every(isFieldValid)) {
            showingValidationError = false;
            setStatus("IDLE", "text-secondary");
        }
    });

    contactForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const invalidFields = validateFields();
        if (invalidFields.length > 0) {
            setStatus("Please fill in every field with a valid email address.", "text-error");
            showingValidationError = true;
            invalidFields[0].focus();
            return;
        }
        showingValidationError = false;

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

            // The timer keeps running through the body read, so a stalled body
            // also ends in the "may have been sent" message instead of hanging.
            let data = {};
            try {
                data = await response.json();
            } catch (error) {
                if (controller.signal.aborted) {
                    throw error;
                }
            }

            if (response.ok && data.success) {
                markReceived(data.requestId);
            } else {
                setStatus(describeError(data.message), "text-error");
            }
        } catch (error) {
            // The request may have reached the server before the abort, so
            // don't invite a blind resend.
            setStatus(controller.signal.aborted ? UNCERTAIN_ERROR : "Network error. Please try again.", "text-error");
        } finally {
            clearTimeout(timeoutId);
            submitButton.disabled = false;
            contactForm.removeAttribute("aria-busy");
        }
    });
});
