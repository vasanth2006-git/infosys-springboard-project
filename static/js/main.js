// ShopSense Common JavaScript Helpers

document.addEventListener("DOMContentLoaded", () => {
    // Show/Hide password toggle logic
    const passwordToggles = document.querySelectorAll(".password-toggle");
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = toggle.getAttribute("data-target");
            const passwordInput = document.getElementById(targetId);
            const icon = toggle.querySelector("i");
            
            if (passwordInput && icon) {
                if (passwordInput.type === "password") {
                    passwordInput.type = "text";
                    icon.classList.remove("fa-eye");
                    icon.classList.add("fa-eye-slash");
                } else {
                    passwordInput.type = "password";
                    icon.classList.remove("fa-eye-slash");
                    icon.classList.add("fa-eye");
                }
            }
        });
    });
});

// Helper function to display form errors
function showError(message) {
    const errorEl = document.getElementById("errorMessage");
    const errorTextEl = document.getElementById("errorText");
    if (errorEl) {
        if (errorTextEl) {
            errorTextEl.textContent = message;
        } else {
            errorEl.textContent = message;
        }
        errorEl.style.display = "flex";
        
        // Auto scroll to top of form
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// Helper to hide form errors
function clearError() {
    const errorEl = document.getElementById("errorMessage");
    const errorTextEl = document.getElementById("errorText");
    if (errorEl) {
        errorEl.style.display = "none";
        if (errorTextEl) {
            errorTextEl.textContent = "";
        } else {
            errorEl.textContent = "";
        }
    }
}
