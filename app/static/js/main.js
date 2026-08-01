document.addEventListener('DOMContentLoaded', () => {

    // ==========================================================================
    // 1. LOGIN PAGE LOGIC
    // ==========================================================================
    const roleSelector = document.getElementById('roleSelector');
    const vendorRoleBtn = document.getElementById('vendorRoleBtn');
    const adminRoleBtn = document.getElementById('adminRoleBtn');
    const selectedRoleInput = document.getElementById('selectedRole');
    const submitLoginBtn = document.getElementById('submitLoginBtn');
    const loginForm = document.getElementById('loginForm');
    const alertBox = document.getElementById('alertBox');
    const alertMessage = document.getElementById('alertMessage');
    const passwordToggle = document.getElementById('passwordToggle');
    const eyeIcon = document.getElementById('eyeIcon');
    const passwordInput = document.getElementById('password');

    if (roleSelector) {
        // Toggle role selection
        vendorRoleBtn.addEventListener('click', () => {
            vendorRoleBtn.classList.add('active');
            adminRoleBtn.classList.remove('active');
            selectedRoleInput.value = 'vendor';
            submitLoginBtn.querySelector('span').textContent = 'Sign in as Vendor';
            hideAlert();
        });

        adminRoleBtn.addEventListener('click', () => {
            adminRoleBtn.classList.add('active');
            vendorRoleBtn.classList.remove('active');
            selectedRoleInput.value = 'admin';
            submitLoginBtn.querySelector('span').textContent = 'Sign in as Admin';
            hideAlert();
        });

        // Eye Icon Password Toggle
        if (passwordToggle && passwordInput) {
            passwordToggle.addEventListener('click', () => {
                const isPassword = passwordInput.getAttribute('type') === 'password';
                passwordInput.setAttribute('type', isPassword ? 'text' : 'password');
                eyeIcon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            });
        }

        // Login Form Submission
        if (loginForm) {
            loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                hideAlert();

                const email = document.getElementById('email').value.trim();
                const password = passwordInput.value;
                const role = selectedRoleInput.value;

                if (!email || !password) {
                    showAlert('Please fill in all required fields.');
                    return;
                }

                if (password.length < 6) {
                    showAlert('Password must be at least 6 characters.');
                    return;
                }

                try {
                    const response = await fetch('/api/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password, role })
                    });

                    const data = await response.json();

                    if (response.ok && data.success) {
                        window.location.href = data.redirect_url;
                    } else {
                        showAlert(data.detail || 'Login failed. Please check your credentials.');
                    }
                } catch (err) {
                    showAlert('Network error. Please try again later.');
                }
            });
        }
    }

    function showAlert(msg) {
        if (alertBox && alertMessage) {
            alertMessage.textContent = msg;
            alertBox.classList.remove('hidden');
        }
    }

    function hideAlert() {
        if (alertBox) {
            alertBox.classList.add('hidden');
        }
    }


    // ==========================================================================
    // 2. VENDOR REGISTRATION PAGE LOGIC
    // ==========================================================================
    const registerForm = document.getElementById('registerForm');
    const regAlertBox = document.getElementById('regAlertBox');
    const regAlertMessage = document.getElementById('regAlertMessage');
    const regPasswordToggle = document.getElementById('regPasswordToggle');
    const regPassword = document.getElementById('regPassword');
    const regEyeIcon = document.getElementById('regEyeIcon');
    const registrationCard = document.getElementById('registrationCard');
    const confirmationCard = document.getElementById('confirmationCard');

    if (registerForm) {
        // Password Eye Toggle
        if (regPasswordToggle && regPassword) {
            regPasswordToggle.addEventListener('click', () => {
                const isPassword = regPassword.getAttribute('type') === 'password';
                regPassword.setAttribute('type', isPassword ? 'text' : 'password');
                regEyeIcon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            });
        }

        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (regAlertBox) regAlertBox.classList.add('hidden');

            const fullName = document.getElementById('fullName').value.trim();
            const businessName = document.getElementById('businessName').value.trim();
            const email = document.getElementById('regEmail').value.trim();
            const password = regPassword.value;
            const phone = document.getElementById('phone').value.trim();
            const address = document.getElementById('address').value.trim();

            if (!fullName || !businessName || !email || !password) {
                showRegAlert('Please fill in all required fields (*).');
                return;
            }

            if (password.length < 6) {
                showRegAlert('Password must be at least 6 characters long.');
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: fullName,
                        business_name: businessName,
                        email: email,
                        password: password,
                        phone: phone || null,
                        address: address || null
                    })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    // Show post-registration confirmation card
                    registrationCard.classList.add('hidden');
                    confirmationCard.classList.remove('hidden');
                } else {
                    showRegAlert(data.detail || 'Registration failed. Please try again.');
                }
            } catch (err) {
                showRegAlert('Network error. Please try again later.');
            }
        });
    }

    function showRegAlert(msg) {
        if (regAlertBox && regAlertMessage) {
            regAlertMessage.textContent = msg;
            regAlertBox.classList.remove('hidden');
        }
    }


    // ==========================================================================
    // 3. ADMIN DASHBOARD & VENDOR MANAGEMENT LOGIC
    // ==========================================================================
    const dashboardTab = document.getElementById('dashboardTab');
    const vendorMgmtTab = document.getElementById('vendorMgmtTab');
    const navDashboard = document.getElementById('navDashboard');
    const navVendorMgmt = document.getElementById('navVendorMgmt');

    const totalVendorsCount = document.getElementById('totalVendorsCount');
    const pendingVendorsCount = document.getElementById('pendingVendorsCount');
    const approvedVendorsCount = document.getElementById('approvedVendorsCount');
    const suspendedVendorsCount = document.getElementById('suspendedVendorsCount');

    const recentVendorsTableBody = document.getElementById('recentVendorsTableBody');
    const vendorMgmtTableBody = document.getElementById('vendorMgmtTableBody');
    const vendorSearchInput = document.getElementById('vendorSearchInput');
    const statusFilterSelect = document.getElementById('statusFilterSelect');

    // Confirmation Modal Elements
    const confirmationModal = document.getElementById('confirmationModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const modalCancelBtn = document.getElementById('modalCancelBtn');
    const modalConfirmBtn = document.getElementById('modalConfirmBtn');
    const toastNotification = document.getElementById('toastNotification');
    const toastMessage = document.getElementById('toastMessage');

    let allVendors = [];
    let activeVendorTarget = null; // { id, business_name, targetStatus }

    if (dashboardTab) {
        // Tab switching
        navDashboard.addEventListener('click', (e) => {
            e.preventDefault();
            navDashboard.classList.add('active');
            navVendorMgmt.classList.remove('active');
            dashboardTab.classList.remove('hidden');
            vendorMgmtTab.classList.add('hidden');
            loadAdminData();
        });

        navVendorMgmt.addEventListener('click', (e) => {
            e.preventDefault();
            navVendorMgmt.classList.add('active');
            navDashboard.classList.remove('active');
            vendorMgmtTab.classList.remove('hidden');
            dashboardTab.classList.add('hidden');
            loadAdminData();
        });

        // Search and Status Filter event listeners
        if (vendorSearchInput) {
            vendorSearchInput.addEventListener('input', renderVendorMgmtTable);
        }
        if (statusFilterSelect) {
            statusFilterSelect.addEventListener('change', renderVendorMgmtTable);
        }

        // Modal Action Listeners
        if (modalCloseBtn) modalCloseBtn.addEventListener('click', hideModal);
        if (modalCancelBtn) modalCancelBtn.addEventListener('click', hideModal);

        if (modalConfirmBtn) {
            modalConfirmBtn.addEventListener('click', async () => {
                if (!activeVendorTarget) return;

                const { id, targetStatus } = activeVendorTarget;
                const endpoint = targetStatus === 'Approved'
                    ? `/api/admin/vendors/${id}/approve`
                    : `/api/admin/vendors/${id}/suspend`;

                try {
                    const res = await fetch(endpoint, { method: 'POST' });
                    const data = await res.json();
                    if (res.ok && data.success) {
                        hideModal();
                        showToast(targetStatus === 'Approved' ? 'Vendor approved successfully.' : 'Vendor suspended successfully.');
                        await loadAdminData();
                    } else {
                        alert(data.detail || 'Failed to update vendor status.');
                    }
                } catch (err) {
                    alert('Error communicating with server.');
                }
            });
        }

        // Initial Data Load
        loadAdminData();
    }

    async function loadAdminData() {
        try {
            // Load metrics & vendors
            const [metricsRes, vendorsRes] = await Promise.all([
                fetch('/api/admin/metrics'),
                fetch('/api/admin/vendors')
            ]);

            if (metricsRes.ok) {
                const metrics = await metricsRes.json();
                if (totalVendorsCount) totalVendorsCount.textContent = metrics.total;
                if (pendingVendorsCount) pendingVendorsCount.textContent = metrics.pending;
                if (approvedVendorsCount) approvedVendorsCount.textContent = metrics.approved;
                if (suspendedVendorsCount) suspendedVendorsCount.textContent = metrics.suspended;
            }

            if (vendorsRes.ok) {
                allVendors = await vendorsRes.json();
                renderRecentVendorsTable();
                renderVendorMgmtTable();
            }
        } catch (err) {
            console.error('Error loading admin data:', err);
        }
    }

    function renderRecentVendorsTable() {
        if (!recentVendorsTableBody) return;

        if (allVendors.length === 0) {
            recentVendorsTableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="text-center py-4 text-muted">No vendors registered yet.</td>
                </tr>
            `;
            return;
        }

        const recent = allVendors.slice(0, 5);
        recentVendorsTableBody.innerHTML = recent.map(v => `
            <tr>
                <td><strong>${escapeHtml(v.full_name)}</strong></td>
                <td>${escapeHtml(v.business_name)}</td>
                <td>${escapeHtml(v.email)}</td>
                <td><span class="badge badge-${v.status.toLowerCase()}">${v.status}</span></td>
                <td>${v.created_at}</td>
            </tr>
        `).join('');
    }

    function renderVendorMgmtTable() {
        if (!vendorMgmtTableBody) return;

        const query = (vendorSearchInput ? vendorSearchInput.value : '').toLowerCase().trim();
        const selectedStatus = statusFilterSelect ? statusFilterSelect.value : 'All';

        const filtered = allVendors.filter(v => {
            const matchesQuery = !query || 
                v.full_name.toLowerCase().includes(query) ||
                v.business_name.toLowerCase().includes(query) ||
                v.email.toLowerCase().includes(query);

            const matchesStatus = (selectedStatus === 'All') || (v.status === selectedStatus);

            return matchesQuery && matchesStatus;
        });

        if (filtered.length === 0) {
            vendorMgmtTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4 text-muted">No matching vendors found.</td>
                </tr>
            `;
            return;
        }

        vendorMgmtTableBody.innerHTML = filtered.map(v => {
            let actionButtonsHTML = '';
            if (v.status === 'Pending') {
                actionButtonsHTML = `
                    <button class="btn-action-approve" onclick="triggerStatusModal(${v.id}, '${escapeQuote(v.business_name)}', 'Approved')">Approve</button>
                    <button class="btn-action-suspend" onclick="triggerStatusModal(${v.id}, '${escapeQuote(v.business_name)}', 'Suspended')">Suspend</button>
                `;
            } else if (v.status === 'Approved') {
                actionButtonsHTML = `
                    <button class="btn-action-suspend" onclick="triggerStatusModal(${v.id}, '${escapeQuote(v.business_name)}', 'Suspended')">Suspend</button>
                `;
            } else if (v.status === 'Suspended') {
                actionButtonsHTML = `
                    <button class="btn-action-approve" onclick="triggerStatusModal(${v.id}, '${escapeQuote(v.business_name)}', 'Approved')">Approve</button>
                `;
            }

            return `
                <tr>
                    <td><strong>${escapeHtml(v.full_name)}</strong></td>
                    <td>${escapeHtml(v.business_name)}</td>
                    <td>${escapeHtml(v.email)}</td>
                    <td><span class="badge badge-${v.status.toLowerCase()}">${v.status}</span></td>
                    <td>${v.created_at}</td>
                    <td><div class="table-actions">${actionButtonsHTML}</div></td>
                </tr>
            `;
        }).join('');
    }

    // Modal & Toast Helpers
    window.triggerStatusModal = (id, businessName, targetStatus) => {
        activeVendorTarget = { id, businessName, targetStatus };
        if (targetStatus === 'Approved') {
            modalTitle.textContent = 'Approve Vendor';
            modalMessage.textContent = `Are you sure you want to approve '${businessName}'?`;
            modalConfirmBtn.textContent = 'Approve Vendor';
            modalConfirmBtn.className = 'btn btn-primary';
        } else {
            modalTitle.textContent = 'Suspend Vendor';
            modalMessage.textContent = `Are you sure you want to suspend '${businessName}'?`;
            modalConfirmBtn.textContent = 'Suspend Vendor';
            modalConfirmBtn.className = 'btn btn-action-suspend';
        }

        confirmationModal.classList.remove('hidden');
    };

    function hideModal() {
        if (confirmationModal) confirmationModal.classList.add('hidden');
        activeVendorTarget = null;
    }

    function showToast(msg) {
        if (toastNotification && toastMessage) {
            toastMessage.textContent = msg;
            toastNotification.classList.remove('hidden');
            setTimeout(() => {
                toastNotification.classList.add('hidden');
            }, 3000);
        }
    }

    function escapeHtml(str) {
        return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function escapeQuote(str) {
        return (str || '').replace(/'/g, "\\'");
    }

    // ==========================================================================
    // 4. VENDOR DASHBOARD LOGIC
    // ==========================================================================
    const viewDashboard = document.getElementById('viewDashboard');
    const viewCatalog = document.getElementById('viewCatalog');
    const viewAddProduct = document.getElementById('viewAddProduct');
    const viewInsights = document.getElementById('viewInsights');
    const viewProfile = document.getElementById('viewProfile');

    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    const vendorLogoutBtn = document.getElementById('vendorLogoutBtn');

    // Dashboard dynamic elements
    const vendorWelcomeName = document.getElementById('vendorWelcomeName');
    const sidebarVendorName = document.getElementById('sidebarVendorName');
    const sidebarBusinessName = document.getElementById('sidebarBusinessName');

    const cardTotalSales = document.getElementById('cardTotalSales');
    const cardTotalRevenue = document.getElementById('cardTotalRevenue');
    const cardTotalTransactions = document.getElementById('cardTotalTransactions');
    const cardPublishedProducts = document.getElementById('cardPublishedProducts');

    const recentProductsContainer = document.getElementById('recentProductsContainer');
    const recentProductsTbody = document.getElementById('recentProductsTbody');
    const emptyProductsState = document.getElementById('emptyProductsState');

    // Catalog & Form elements
    const fullCatalogTbody = document.getElementById('fullCatalogTbody');
    const catalogSearchInput = document.getElementById('catalogSearchInput');
    const productForm = document.getElementById('productForm');
    const btnGenerateAiDesc = document.getElementById('btnGenerateAiDesc');
    const vendorProfileForm = document.getElementById('vendorProfileForm');

    const vendorToast = document.getElementById('vendorToast');
    const vendorToastMsg = document.getElementById('vendorToastMsg');

    let allVendorProducts = [];

    // Switch view helper
    window.switchToView = (viewName) => {
        const views = {
            'dashboard': viewDashboard,
            'catalog': viewCatalog,
            'add-product': viewAddProduct,
            'insights': viewInsights,
            'profile': viewProfile
        };

        // Reset sidebar active states
        sidebarLinks.forEach(link => {
            if (link.getAttribute('data-view') === viewName) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });

        // Hide all views, show requested view
        Object.keys(views).forEach(k => {
            if (views[k]) {
                if (k === viewName) {
                    views[k].classList.remove('hidden');
                    views[k].classList.add('active');
                } else {
                    views[k].classList.add('hidden');
                    views[k].classList.remove('active');
                }
            }
        });

        // Reload data if switching to dashboard or catalog
        if (viewName === 'dashboard') {
            loadVendorDashboardData();
        } else if (viewName === 'catalog') {
            loadCatalogData();
        } else if (viewName === 'profile') {
            loadVendorProfile();
        } else if (viewName === 'insights') {
            // Initialize Sales Trends chart with active tab period
            setTimeout(function() {
                if (typeof initSalesChart === 'function') {
                    const activeTab = document.querySelector('#salesTrendTabs .trend-tab.active');
                    const period = activeTab ? activeTab.dataset.period : 'daily';
                    initSalesChart(period);
                }
            }, 60);
        } else if (viewName === 'add-product') {
            // Reset form for fresh product creation
            const editId = document.getElementById('editProductId');
            if (editId && editId.value) {
                editId.value = '';
                document.getElementById('productFormTitle').textContent = 'Add New Product';
                productForm.reset();
            }
        }
    };

    if (viewDashboard) {
        // Sidebar Navigation click handlers
        sidebarLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetView = link.getAttribute('data-view');
                if (targetView) {
                    switchToView(targetView);
                }
            });
        });

        // Logout handler
        if (vendorLogoutBtn) {
            vendorLogoutBtn.addEventListener('click', async () => {
                try {
                    const res = await fetch('/api/logout', { method: 'POST' });
                    const data = await res.json();
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    }
                } catch (err) {
                    window.location.href = '/login';
                }
            });
        }

        // Product Form submit handler
        if (productForm) {
            productForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const editId = document.getElementById('editProductId').value;
                const name = document.getElementById('productName').value.trim();
                const category = document.getElementById('productCategory').value;
                const price = parseFloat(document.getElementById('productPrice').value);
                const stock = parseInt(document.getElementById('productStock').value, 10);
                const image_url = document.getElementById('productImageUrl').value.trim();
                const description = document.getElementById('productDescription').value.trim();

                if (!name || !category || isNaN(price) || isNaN(stock)) {
                    showVendorToast('Please fill in all required fields (*).', true);
                    return;
                }

                const payload = { name, category, price, stock, image_url: image_url || null, description: description || null };
                const endpoint = editId ? `/api/vendor/products/${editId}` : '/api/vendor/products';
                const method = editId ? 'PUT' : 'POST';

                try {
                    const res = await fetch(endpoint, {
                        method: method,
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        showVendorToast(editId ? 'Product updated successfully!' : 'Product added successfully!');
                        productForm.reset();
                        document.getElementById('editProductId').value = '';
                        switchToView('dashboard');
                    } else {
                        showVendorToast(data.detail || 'Failed to save product.', true);
                    }
                } catch (err) {
                    showVendorToast('Network error while saving product.', true);
                }
            });
        }

        // AI Description Generator Button
        if (btnGenerateAiDesc) {
            btnGenerateAiDesc.addEventListener('click', async () => {
                const name = document.getElementById('productName').value.trim();
                const category = document.getElementById('productCategory').value;

                if (!name || !category) {
                    showVendorToast('Please enter Product Name & select Category first.', true);
                    return;
                }

                btnGenerateAiDesc.disabled = true;
                btnGenerateAiDesc.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';

                try {
                    const res = await fetch('/api/vendor/generate-description', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, category })
                    });
                    const data = await res.json();

                    if (res.ok && data.description) {
                        document.getElementById('productDescription').value = data.description;
                        showVendorToast('AI Description generated!');
                    }
                } catch (err) {
                    showVendorToast('Failed to generate AI description.', true);
                } finally {
                    btnGenerateAiDesc.disabled = false;
                    btnGenerateAiDesc.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generate with AI';
                }
            });
        }

        // Catalog Search Input
        if (catalogSearchInput) {
            catalogSearchInput.addEventListener('input', renderFullCatalogTable);
        }

        // Vendor Profile Form submit handler
        if (vendorProfileForm) {
            vendorProfileForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const full_name = document.getElementById('profFullName').value.trim();
                const business_name = document.getElementById('profBusinessName').value.trim();
                const phone = document.getElementById('profPhone').value.trim();
                const address = document.getElementById('profAddress').value.trim();
                const new_password = document.getElementById('profNewPassword').value.trim();

                try {
                    const res = await fetch('/api/vendor/profile', {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ full_name, business_name, phone, address, new_password: new_password || null })
                    });
                    const data = await res.json();

                    if (res.ok && data.success) {
                        showVendorToast('Profile updated successfully!');
                        loadVendorProfile();
                    } else {
                        showVendorToast(data.detail || 'Failed to update profile.', true);
                    }
                } catch (err) {
                    showVendorToast('Error updating profile.', true);
                }
            });
        }

        // Initial dashboard data load
        loadVendorDashboardData();
    }

    // Load Dashboard Summary Cards & Recent Products
    async function loadVendorDashboardData() {
        try {
            const res = await fetch('/api/vendor/dashboard-data');
            if (!res.ok) return;

            const data = await res.json();

            // Populate Vendor Name in header & welcome message
            if (vendorWelcomeName) vendorWelcomeName.textContent = data.vendor_name;
            if (sidebarVendorName) sidebarVendorName.textContent = data.vendor_name;
            if (sidebarBusinessName) sidebarBusinessName.textContent = data.business_name || 'Approved';

            // Populate Summary Cards
            if (cardTotalSales) cardTotalSales.textContent = data.total_sales.toLocaleString();
            if (cardTotalRevenue) {
                cardTotalRevenue.textContent = '$' + data.total_revenue.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
            }
            if (cardTotalTransactions) cardTotalTransactions.textContent = data.total_transactions.toLocaleString();
            if (cardPublishedProducts) cardPublishedProducts.textContent = data.published_products.toLocaleString();

            // Render Recent Products or Empty State
            const products = data.recent_products || [];
            if (products.length === 0) {
                if (recentProductsContainer) recentProductsContainer.classList.add('hidden');
                if (emptyProductsState) emptyProductsState.classList.remove('hidden');
            } else {
                if (emptyProductsState) emptyProductsState.classList.add('hidden');
                if (recentProductsContainer) recentProductsContainer.classList.remove('hidden');
                renderRecentProductsTable(products);
            }
        } catch (err) {
            console.error('Error loading vendor dashboard data:', err);
        }
    }

    // Render Recent Products Table (Product image, name, AI description, Category, Price, Stock)
    function renderRecentProductsTable(products) {
        if (!recentProductsTbody) return;

        const defaultImg = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150&auto=format&fit=crop&q=80';

        recentProductsTbody.innerHTML = products.map(p => {
            const imgUrl = p.image_url && p.image_url.trim() ? p.image_url : defaultImg;
            let stockBadgeClass = 'stock-in';
            if (p.stock === 0) stockBadgeClass = 'stock-out';
            else if (p.stock <= 5) stockBadgeClass = 'stock-low';

            return `
                <tr>
                    <td>
                        <div class="product-cell">
                            <img src="${escapeHtml(imgUrl)}" alt="${escapeHtml(p.name)}" class="product-thumb" onerror="this.src='${defaultImg}'">
                            <div class="product-info">
                                <span class="product-title">${escapeHtml(p.name)}</span>
                                <p class="product-desc">${escapeHtml(p.description || 'AI-generated product details')}</p>
                            </div>
                        </div>
                    </td>
                    <td><span class="category-pill">${escapeHtml(p.category)}</span></td>
                    <td><span class="price-text">$${p.price.toFixed(2)}</span></td>
                    <td><span class="stock-badge ${stockBadgeClass}">${p.stock} units</span></td>
                </tr>
            `;
        }).join('');
    }

    // Load catalog list
    async function loadCatalogData() {
        try {
            const res = await fetch('/api/vendor/products');
            if (res.ok) {
                allVendorProducts = await res.json();
                renderFullCatalogTable();
            }
        } catch (err) {
            console.error('Error loading catalog:', err);
        }
    }

    function renderFullCatalogTable() {
        if (!fullCatalogTbody) return;
        const query = (catalogSearchInput ? catalogSearchInput.value : '').toLowerCase().trim();

        const filtered = allVendorProducts.filter(p => {
            return !query ||
                p.name.toLowerCase().includes(query) ||
                p.category.toLowerCase().includes(query);
        });

        if (filtered.length === 0) {
            fullCatalogTbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4">
                        <div class="empty-state-box" style="margin: 0;">
                            <div class="empty-icon"><i class="fa-solid fa-box-open"></i></div>
                            <p class="empty-message">No products found.</p>
                            <button class="btn btn-primary" onclick="switchToView('add-product')">
                                <i class="fa-solid fa-plus"></i> Add Product
                            </button>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        const defaultImg = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150&auto=format&fit=crop&q=80';

        fullCatalogTbody.innerHTML = filtered.map(p => {
            const imgUrl = p.image_url && p.image_url.trim() ? p.image_url : defaultImg;
            const statusBadgeHTML = p.stock > 0 
                ? '<span class="stock-badge stock-in">Active</span>'
                : '<span class="stock-badge stock-out">Out of Stock</span>';

            return `
                <tr>
                    <td>
                        <div class="product-cell">
                            <img src="${escapeHtml(imgUrl)}" alt="${escapeHtml(p.name)}" class="product-thumb" onerror="this.src='${defaultImg}'">
                            <div class="product-info">
                                <span class="product-title">${escapeHtml(p.name)}</span>
                                <p class="product-desc">${escapeHtml(p.description || 'AI-generated product details')}</p>
                            </div>
                        </div>
                    </td>
                    <td><span class="category-pill">${escapeHtml(p.category)}</span></td>
                    <td><span class="price-text">$${p.price.toFixed(2)}</span></td>
                    <td>${p.stock}</td>
                    <td>${statusBadgeHTML}</td>
                    <td>
                        <div class="table-actions">
                            <button class="btn-action-view" onclick="viewProduct(${p.id})"><i class="fa-solid fa-eye"></i> View</button>
                            <button class="btn-action-approve" onclick="editProduct(${p.id})"><i class="fa-solid fa-pen-to-square"></i> Edit</button>
                            <button class="btn-action-suspend" onclick="deleteProduct(${p.id})"><i class="fa-solid fa-trash"></i> Delete</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    }

    // Global view product trigger
    window.viewProduct = (productId) => {
        const prod = allVendorProducts.find(p => p.id === productId);
        if (!prod) return;

        const defaultImg = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=150&auto=format&fit=crop&q=80';
        const modal = document.getElementById('productViewModal');
        const modalTitle = document.getElementById('viewModalTitle');
        const modalImg = document.getElementById('viewModalImg');
        const modalName = document.getElementById('viewModalName');
        const modalCat = document.getElementById('viewModalCategory');
        const modalPrice = document.getElementById('viewModalPrice');
        const modalStock = document.getElementById('viewModalStock');
        const modalDesc = document.getElementById('viewModalDesc');

        const closeBtn1 = document.getElementById('viewModalCloseBtn');
        const closeBtn2 = document.getElementById('viewModalCloseBtn2');
        const editBtn = document.getElementById('viewModalEditBtn');

        if (modal) {
            modalTitle.textContent = prod.name;
            modalImg.src = prod.image_url && prod.image_url.trim() ? prod.image_url : defaultImg;
            modalName.textContent = prod.name;
            modalCat.textContent = prod.category;
            modalPrice.textContent = `$${prod.price.toFixed(2)}`;
            modalStock.textContent = prod.stock > 0 ? `Active (${prod.stock} in stock)` : 'Out of Stock';
            modalStock.className = prod.stock > 0 ? 'stock-badge stock-in ms-2' : 'stock-badge stock-out ms-2';
            modalDesc.textContent = prod.description || 'No description provided.';

            const hideViewModal = () => modal.classList.add('hidden');
            if (closeBtn1) closeBtn1.onclick = hideViewModal;
            if (closeBtn2) closeBtn2.onclick = hideViewModal;
            if (editBtn) editBtn.onclick = () => {
                hideViewModal();
                editProduct(prod.id);
            };

            modal.classList.remove('hidden');
        }
    };

    // Global edit product trigger
    window.editProduct = (productId) => {
        const prod = allVendorProducts.find(p => p.id === productId);
        if (!prod) return;

        document.getElementById('editProductId').value = prod.id;
        document.getElementById('productName').value = prod.name;
        document.getElementById('productCategory').value = prod.category;
        document.getElementById('productPrice').value = prod.price;
        document.getElementById('productStock').value = prod.stock;
        document.getElementById('productImageUrl').value = prod.image_url || '';
        document.getElementById('productDescription').value = prod.description || '';
        document.getElementById('productFormTitle').textContent = 'Edit Product';

        switchToView('add-product');
    };

    // Global delete product trigger
    window.deleteProduct = async (productId) => {
        if (!confirm('Are you sure you want to delete this product?')) return;

        try {
            const res = await fetch(`/api/vendor/products/${productId}`, { method: 'DELETE' });
            const data = await res.json();
            if (res.ok && data.success) {
                showVendorToast('Product deleted.');
                loadCatalogData();
                loadVendorDashboardData();
            } else {
                showVendorToast('Failed to delete product.', true);
            }
        } catch (err) {
            showVendorToast('Error deleting product.', true);
        }
    };

    // Load vendor profile data into form
    async function loadVendorProfile() {
        try {
            const res = await fetch('/api/vendor/me');
            if (res.ok) {
                const vendor = await res.json();
                document.getElementById('profFullName').value = vendor.full_name || '';
                document.getElementById('profBusinessName').value = vendor.business_name || '';
                document.getElementById('profEmail').value = vendor.email || '';
                document.getElementById('profPhone').value = vendor.phone || '';
                document.getElementById('profAddress').value = vendor.address || '';
            }
        } catch (err) {
            console.error('Error loading vendor profile:', err);
        }
    }

    function showVendorToast(msg, isError = false) {
        if (vendorToast && vendorToastMsg) {
            vendorToastMsg.textContent = msg;
            if (isError) {
                vendorToast.style.background = '#ef4444';
            } else {
                vendorToast.style.background = '#10b981';
            }
            vendorToast.classList.remove('hidden');
            setTimeout(() => {
                vendorToast.classList.add('hidden');
            }, 3000);
        }
    }
});


