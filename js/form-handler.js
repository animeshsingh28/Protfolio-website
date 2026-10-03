document.addEventListener("DOMContentLoaded", () => {
    const contactSection = document.getElementById("contact");
    const contactForm = contactSection?.querySelector("form");
    const submitButton = contactForm?.querySelector("button[type='submit']");
    const statusNode = document.getElementById("contact-form-status");
    const startedAtInput = contactForm?.querySelector("input[name='form_started_at']");

    if (!contactForm || !submitButton || !statusNode || !startedAtInput) {
        return;
    }

    // Above the function's maxDuration (20s in vercel.json), plus cold-start
    // margin. The server saves the message before sending the email, so a
    // timeout is reported as "may have been sent" rather than as a failure.
    const REQUEST_TIMEOUT_MS = 25000;
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

    // The start time stays on the client; only the elapsed seconds are sent,
    // so the visitor's clock never has to agree with the server's.
    const resetStartTime = () => {
        startedAtInput.value = String(Date.now());
    };

    const fillSeconds = () => {
        const startedAt = Number(startedAtInput.value);
        return startedAt > 0 ? Math.max(0, (Date.now() - startedAt) / 1000) : 0;
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
            form_fill_seconds: fillSeconds(),
        };

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

        submitButton.disabled = true;
        contactForm.setAttribute("aria-busy", "true");
        setStatus("TRANSMITTING...", "text-secondary");

        let receivedHeaders = false;
        try {
            const response = await fetch("/api/contact", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });
            receivedHeaders = true;

            // The timer keeps running through the body read, so a stalled body
            // also ends in the "may have been sent" message instead of hanging.
            // Headers mean the server has finished, so a body that fails to
            // arrive (abort or dropped connection) is reported as uncertain.
            // Only a complete body that isn't JSON falls back to an error.
            const text = await response.text();
            let data;
            try {
                data = JSON.parse(text) || {};
            } catch {
                data = null;
            }

            if (response.ok && data?.success) {
                markReceived(data.requestId);
            } else if (!data && response.status >= 500) {
                // A non-JSON 5xx comes from the platform (e.g. the function was
                // stopped at its time limit), possibly after the message was
                // saved, so don't invite a blind resend.
                setStatus(UNCERTAIN_ERROR, "text-error");
            } else {
                setStatus(describeError(data?.message), "text-error");
            }
        } catch (error) {
            // Once headers arrived (or the timeout fired) the request may have
            // reached the server, so don't invite a blind resend.
            setStatus(controller.signal.aborted || receivedHeaders ? UNCERTAIN_ERROR : "Network error. Please try again.", "text-error");
        } finally {
            clearTimeout(timeoutId);
            submitButton.disabled = false;
            contactForm.removeAttribute("aria-busy");
        }
    });
});
