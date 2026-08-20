// Admin Dashboard UI & Business Logic

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------------------
    // 1. Tab Navigation & State Preservation
    // -------------------------------------------------------------
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");

    function switchTab(tabId) {
        // Remove active class from all nav items and hide all tab contents
        navItems.forEach(item => item.classList.remove("active"));
        tabContents.forEach(content => content.style.display = "none");

        // Activate the selected nav item and show corresponding content
        const targetNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
        const targetContent = document.getElementById(tabId);

        if (targetNav && targetContent) {
            targetNav.classList.add("active");
            targetContent.style.display = "block";
            localStorage.setItem("active_admin_tab", tabId);
            window.location.hash = tabId;
        }
    }

    // Initialize tabs from hash, localStorage, or default to 'dashboard-view'
    let defaultTab = window.location.hash.replace("#", "") || localStorage.getItem("active_admin_tab") || "dashboard-view";
    if (defaultTab !== "dashboard-view" && defaultTab !== "vendor-management-view" && defaultTab !== "customer-analytics-view") {
        defaultTab = "dashboard-view";
    }
    switchTab(defaultTab);

    // Bind click events to navigation buttons
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    // -------------------------------------------------------------
    // 2. Real-time Search and Status Filter (Vendor Management Page)
    // -------------------------------------------------------------
    const searchInput = document.getElementById("vendorSearchInput");
    const filterSelect = document.getElementById("statusFilterSelect");
    const vendorRows = document.querySelectorAll(".vendor-row");

    function applySearchAndFilter() {
        const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
        const filterVal = filterSelect ? filterSelect.value.toLowerCase() : "all";

        vendorRows.forEach(row => {
            const name = row.getAttribute("data-name").toLowerCase();
            const business = row.getAttribute("data-business").toLowerCase();
            const email = row.getAttribute("data-email").toLowerCase();
            const status = row.getAttribute("data-status").toLowerCase();

            // Matches search query (Name, Business, Email)
            const matchesSearch = query === "" || 
                                  name.includes(query) || 
                                  business.includes(query) || 
                                  email.includes(query);

            // Matches filter selection
            const matchesFilter = filterVal === "all" || status === filterVal;

            if (matchesSearch && matchesFilter) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", applySearchAndFilter);
    }
    if (filterSelect) {
        filterSelect.addEventListener("change", applySearchAndFilter);
    }

    // -------------------------------------------------------------
    // 3. Confirmation Dialog Modals and Actions
    // -------------------------------------------------------------
    const approveModal = document.getElementById("approveModal");
    const suspendModal = document.getElementById("suspendModal");
    
    let currentVendorId = null;

    // Toast Notification helper
    function showToast(message) {
        const toast = document.getElementById("toastNotification");
        const toastText = document.getElementById("toastMessage");
        if (toast && toastText) {
            toastText.textContent = message;
            toast.classList.add("active");
            
            setTimeout(() => {
                toast.classList.remove("active");
            }, 3000);
        }
    }

    // Modal Close Helper
    function closeModal(modal) {
        modal.classList.remove("active");
        currentVendorId = null;
    }

    // Open Approve Modal
    window.openApproveModal = function(vendorId, businessName) {
        currentVendorId = vendorId;
        const businessNameSpan = document.getElementById("approveBusinessName");
        if (businessNameSpan) businessNameSpan.textContent = businessName;
        approveModal.classList.add("active");
    };

    // Open Suspend Modal
    window.openSuspendModal = function(vendorId, businessName) {
        currentVendorId = vendorId;
        const businessNameSpan = document.getElementById("suspendBusinessName");
        if (businessNameSpan) businessNameSpan.textContent = businessName;
        suspendModal.classList.add("active");
    };

    // Close buttons binding
    document.querySelectorAll(".close-modal-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            closeModal(approveModal);
            closeModal(suspendModal);
        });
    });

    // Handle Confirm Approve
    const confirmApproveBtn = document.getElementById("confirmApproveBtn");
    if (confirmApproveBtn) {
        confirmApproveBtn.addEventListener("click", async () => {
            if (!currentVendorId) return;

            try {
                confirmApproveBtn.disabled = true;
                confirmApproveBtn.textContent = "Processing...";

                const response = await fetch(`/admin/vendors/${currentVendorId}/approve`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                if (response.ok) {
                    closeModal(approveModal);
                    showToast("Vendor approved successfully.");
                    // Reload to update stats and table rows
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    const data = await response.json();
                    alert(data.detail || "Failed to approve vendor.");
                    confirmApproveBtn.disabled = false;
                    confirmApproveBtn.textContent = "Approve Vendor";
                }
            } catch (err) {
                console.error(err);
                alert("An error occurred while approving vendor.");
                confirmApproveBtn.disabled = false;
                confirmApproveBtn.textContent = "Approve Vendor";
            }
        });
    }

    // Handle Confirm Suspend
    const confirmSuspendBtn = document.getElementById("confirmSuspendBtn");
    if (confirmSuspendBtn) {
        confirmSuspendBtn.addEventListener("click", async () => {
            if (!currentVendorId) return;

            try {
                confirmSuspendBtn.disabled = true;
                confirmSuspendBtn.textContent = "Processing...";

                const response = await fetch(`/admin/vendors/${currentVendorId}/suspend`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    }
                });

                if (response.ok) {
                    closeModal(suspendModal);
                    showToast("Vendor suspended successfully.");
                    // Reload to update stats and table rows
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    const data = await response.json();
                    alert(data.detail || "Failed to suspend vendor.");
                    confirmSuspendBtn.disabled = false;
                    confirmSuspendBtn.textContent = "Suspend Vendor";
                }
            } catch (err) {
                console.error(err);
                alert("An error occurred while suspending vendor.");
                confirmSuspendBtn.disabled = false;
                confirmSuspendBtn.textContent = "Suspend Vendor";
            }
        });
    }
});
