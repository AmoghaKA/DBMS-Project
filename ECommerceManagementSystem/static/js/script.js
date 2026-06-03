document.addEventListener('DOMContentLoaded', () => {
    // 1. Delete Confirmations
    document.addEventListener('click', (e) => {
        // Target buttons with data-confirm-delete attribute or forms containing them
        if (e.target && e.target.hasAttribute('data-confirm-delete')) {
            const message = e.target.getAttribute('data-confirm-message') || 'Are you sure you want to delete this record?';
            if (!confirm(message)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });

    // 2. Client-side Form Validation
    document.addEventListener('submit', (e) => {
        if (e.target && e.target.classList.contains('js-validate')) {
            let isValid = true;
            const requiredFields = e.target.querySelectorAll('[required]');

            requiredFields.forEach(field => {
                const val = field.value.trim();
                
                // Check if empty
                if (!val) {
                    isValid = false;
                    field.classList.add('invalid-field');
                    showErrorTip(field, 'This field is required.');
                } else {
                    field.classList.remove('invalid-field');
                    removeErrorTip(field);
                }

                // Check Email format
                if (field.type === 'email' && val) {
                    const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
                    if (!emailRegex.test(val)) {
                        isValid = false;
                        field.classList.add('invalid-field');
                        showErrorTip(field, 'Please enter a valid email address.');
                    }
                }

                // Check positive numeric stock/price bounds
                if ((field.type === 'number' || field.classList.contains('number-input')) && val) {
                    const num = parseFloat(val);
                    const min = parseFloat(field.getAttribute('min')) || 0;
                    if (isNaN(num) || num < min) {
                        isValid = false;
                        field.classList.add('invalid-field');
                        showErrorTip(field, `Value must be a valid number and at least ${min}.`);
                    }
                }
            });

            if (!isValid) {
                e.preventDefault();
                // Scroll to the first invalid field
                const firstInvalid = e.target.querySelector('.invalid-field');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
        }
    });

    // Form input event listeners to clear error styling upon typing
    document.addEventListener('input', (e) => {
        if (e.target && e.target.classList.contains('invalid-field')) {
            e.target.classList.remove('invalid-field');
            removeErrorTip(e.target);
        }
    });

    // Helper functions for inline error tooltips
    function showErrorTip(element, msg) {
        removeErrorTip(element); // Remove if exists
        const parent = element.parentElement;
        const errorTip = document.createElement('span');
        errorTip.className = 'field-error-tip';
        errorTip.style.color = '#f43f5e';
        errorTip.style.fontSize = '0.75rem';
        errorTip.style.marginTop = '0.2rem';
        errorTip.innerText = msg;
        parent.appendChild(errorTip);
    }

    function removeErrorTip(element) {
        const parent = element.parentElement;
        const existingTip = parent.querySelector('.field-error-tip');
        if (existingTip) {
            parent.removeChild(existingTip);
        }
    }

    // 3. Instant Search Filtering on Tables
    document.addEventListener('input', (e) => {
        if (e.target && e.target.hasAttribute('data-search-input')) {
            const query = e.target.value.toLowerCase();
            const tableWrap = document.querySelector('[data-search-table]');
            if (tableWrap) {
                const tbody = tableWrap.querySelector('tbody');
                if (tbody) {
                    const rows = tbody.querySelectorAll('tr');
                    let visibleRows = 0;
                    
                    rows.forEach(row => {
                        // Check if it's the empty state row
                        if (row.querySelector('.empty-state')) {
                            return;
                        }
                        
                        const text = row.textContent.toLowerCase();
                        if (text.includes(query)) {
                            row.style.display = '';
                            visibleRows++;
                        } else {
                            row.style.display = 'none';
                        }
                    });

                    // Manage dynamic empty state inside filter search results
                    let dynamicEmptyRow = tbody.querySelector('.search-empty-state');
                    if (visibleRows === 0 && query !== '') {
                        if (!dynamicEmptyRow) {
                            dynamicEmptyRow = document.createElement('tr');
                            dynamicEmptyRow.className = 'search-empty-state';
                            dynamicEmptyRow.innerHTML = `<td colspan="100%" class="empty-state" style="text-align: center; color: #64748b;">No matching records found.</td>`;
                            tbody.appendChild(dynamicEmptyRow);
                        }
                    } else if (dynamicEmptyRow) {
                        tbody.removeChild(dynamicEmptyRow);
                    }
                }
            }
        }
    });

    // 4. Dynamic Subtotal Calculation & Stock Preview on Order Forms
    function calculateSubtotal() {
        const productSelect = document.querySelector('[data-product-selector]');
        const qtyInput = document.querySelector('[data-quantity-input]');
        const subtotalDisplay = document.querySelector('[data-subtotal-display]');
        const stockDisplay = document.querySelector('[data-stock-display]');

        if (productSelect && qtyInput && subtotalDisplay) {
            const selectedOption = productSelect.options[productSelect.selectedIndex];
            
            if (selectedOption && selectedOption.value) {
                const price = parseFloat(selectedOption.getAttribute('data-price')) || 0;
                const stock = parseInt(selectedOption.getAttribute('data-stock')) || 0;
                const qty = parseInt(qtyInput.value) || 0;
                
                // Limit quantity to stock
                qtyInput.setAttribute('max', stock);
                if (stockDisplay) {
                    stockDisplay.textContent = stock;
                }

                const subtotal = price * qty;
                subtotalDisplay.textContent = subtotal.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });

                if (qty > stock) {
                    qtyInput.style.borderColor = '#fbbf24'; // Warning border style
                } else {
                    qtyInput.style.borderColor = '';
                }
            } else {
                subtotalDisplay.textContent = '0.00';
                if (stockDisplay) {
                    stockDisplay.textContent = '0';
                }
                qtyInput.removeAttribute('max');
            }
        }
    }

    // Trigger calculation listeners
    const productSelector = document.querySelector('[data-product-selector]');
    const quantityInput = document.querySelector('[data-quantity-input]');

    if (productSelector && quantityInput) {
        productSelector.addEventListener('change', calculateSubtotal);
        quantityInput.addEventListener('input', calculateSubtotal);
        // Initial call
        calculateSubtotal();
    }
});
