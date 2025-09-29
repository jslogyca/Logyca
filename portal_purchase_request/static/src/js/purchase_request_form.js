/* Purchase Request Form JavaScript */

document.addEventListener('DOMContentLoaded', function() {
    let lineCounter = 1;
    let selectedApprovers = new Set();

        // Initialize form data from preserved values (after validation errors)
        initializeFormData();
        initializeApproversWidget();
        initializeCollaboratorWidget();

        // Auto-update analytic_distribution when budget_group_id changes
        function initAnalyticDistribution() {
            var bg = document.getElementById('budget_group_id');
            var analyticInput = document.getElementById('analytic_distribution');
            if (!bg || !analyticInput) { return; }
            function parseRawToObject(raw) {
                if (!raw) return null;
                var s = String(raw);
                try { return JSON.parse(s); } catch (e) {}
                try { return JSON.parse(s.replace(/\bNone\b/g, 'null').replace(/'/g, '"')); } catch (e) {}
                return null;
            }

            function loadAnalyticAccountsMap() {
                var node = document.getElementById('analytic-accounts-data');
                try {
                    return node ? JSON.parse(node.textContent || node.innerText || '{}') : {};
                } catch (e) { return {}; }
            }

            var acctMap = loadAnalyticAccountsMap();

            function formatDistribution(raw) {
                if (!raw) return '';
                var parsed = parseRawToObject(raw);
                if (!parsed) return String(raw);
                var parts = [];
                for (var k in parsed) {
                    if (!Object.prototype.hasOwnProperty.call(parsed, k)) continue;
                    var pct = parsed[k];
                    var num = Number(pct);
                    var pctStr = (!isNaN(num) && Math.abs(num - Math.round(num)) < 1e-9) ? String(Math.round(num)) : String(num);
                    var name = acctMap[k] || acctMap[Number(k)] || ('#' + k);
                    parts.push(pctStr + '% ' + name);
                }
                return parts.join(' | ');
            }

            function update() {
                var opt = bg.options[bg.selectedIndex];
                if (!opt) return;
                // Prefer server-provided formatted text if available
                var preformatted = opt.getAttribute('data-analytic-formatted');
                if (preformatted) {
                    analyticInput.value = preformatted || '';
                    var label = document.getElementById('analytic_distribution_label');
                    if (label) {
                        label.textContent = preformatted || '';
                        label.setAttribute('title', preformatted || '');
                        label.style.display = preformatted ? 'inline-block' : 'none';
                    }
                    return;
                }
                var raw = opt.getAttribute('data-analytic') || '';
                var formatted = formatDistribution(raw || '');
                // set hidden value to formatted text (so server receives readable value)
                analyticInput.value = formatted || '';
                // update badge label if present
                var label = document.getElementById('analytic_distribution_label');
                if (label) {
                    label.textContent = formatted || '';
                    label.setAttribute('title', formatted || '');
                    label.style.display = formatted ? 'inline-block' : 'none';
                }
            }
            bg.addEventListener('change', update);
            update();
        }
        initAnalyticDistribution();

    // Form validation
    const form = document.querySelector('form[action="/purchase-request/new"]');
    if (form) {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            const requiredFields = form.querySelectorAll('[required]');

            // Clear previous error messages (client-side only)
            document.querySelectorAll('.client-error-message').forEach(el => el.remove());

            // Validate required fields with field-specific messages when available
            const requiredFieldMessages = {
                'project_total_value': 'Project total value is required',
                'division_id': 'Division is required',
                'team_id': 'Team is required',
                'budget_group_id': 'Budget group is required',
                'request_type': 'Request type is required',
                'collaborator_id_widget': 'Collaborator is required',
                'project_start_date': 'Project start date is required',
                'project_end_date': 'Project end date is required',
                'execution_place': 'Execution place is required',
                'payment_agreement': 'Payment agreement is required',
                'currency_id': 'Currency is required',
                'asset_responsible_id': 'Asset responsible is required'
            };

            function hasServerSideError(field) {
                const target = (field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement) ? field.parentNode : field;
                if (!target) return false;
                // server-side errors are rendered with .invalid-feedback but without .client-error-message
                const serverErrors = target.querySelectorAll('.invalid-feedback:not(.client-error-message)');
                return serverErrors.length > 0;
            }

            // Special-case: if both dates are empty, only show start-date error client-side
            const startField = form.querySelector('#project_start_date');
            const endField = form.querySelector('#project_end_date');
            const bothDatesEmpty = startField && endField && !startField.value && !endField.value;
            if (bothDatesEmpty) {
                isValid = false;
                if (!hasServerSideError(startField)) {
                    showFieldError(startField, requiredFieldMessages['project_start_date'], 'client-error');
                }
                // ensure any client-side error on end is cleared
                if (endField) clearFieldError(endField);
            }

            requiredFields.forEach(field => {
                const empty = !field.value || (field.type === 'select-multiple' && !Array.from(field.selectedOptions).some(opt => opt.value));
                if (empty) {
                    // Only show client-side messages for fields we have explicit messages for
                    const key = field.id || field.name;

                    // If both dates are empty, we already handled the start-field and should skip showing the end-field client message
                    if (bothDatesEmpty && key === 'project_end_date') {
                        // still mark form invalid (already done above), but do not add duplicate client message for end date
                        isValid = false;
                        return;
                    }

                    const message = requiredFieldMessages[key];
                    if (message && !hasServerSideError(field)) {
                        isValid = false;
                        showFieldError(field, message, 'client-error');
                    } else {
                        // If no specific client message, prefer server-side validation; do not show generic client message
                        isValid = false;
                    }
                }
            });

            // Validate approvers
            if (selectedApprovers.size === 0) {
                isValid = false;
                const approversContainer = document.querySelector('.approvers-container');
                if (approversContainer && !hasServerSideError(approversContainer)) {
                    showFieldError(approversContainer, 'At least one approver is required', 'client-error');
                }
            }

            // Validate project dates
            const startDate = document.getElementById('project_start_date');
            const endDate = document.getElementById('project_end_date');

            if (startDate.value && endDate.value) {
                if (new Date(startDate.value) > new Date(endDate.value)) {
                    isValid = false;
                    showFieldError(endDate, 'End date must be after start date', 'client-error');
                }
            }

            // Validate project total value
            const totalValue = document.getElementById('project_total_value');
            if (totalValue.value && parseFloat(totalValue.value) <= 0) {
                isValid = false;
                showFieldError(totalValue, 'Total value must be greater than zero', 'client-error');
            }

            // Validate at least one product line
            const productLines = document.querySelectorAll('input[name^="product_description_"]');
            let hasValidProductLine = false;

            productLines.forEach(input => {
                if (input.value.trim()) {
                    hasValidProductLine = true;
                }
            });

            if (!hasValidProductLine) {
                isValid = false;
                const container = document.getElementById('product-lines-container');
                showFieldError(container, 'At least one product line is required', 'client-error');
            }

            // Validate file size
            const fileInput = document.getElementById('attachments');
            // Require at least one attachment
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                isValid = false;
                // Only show client-side message if server hasn't already shown one
                if (fileInput && !hasServerSideError(fileInput)) {
                    showFieldError(fileInput, 'At least one attachment is required', 'client-error');
                }
            } else if (fileInput && fileInput.files.length > 0) {
                const maxSizeMB = parseInt(document.querySelector('[data-max-size]')?.dataset.maxSize || '10');
                const maxSizeBytes = maxSizeMB * 1024 * 1024;
                let totalSize = 0;

                for (let file of fileInput.files) {
                    totalSize += file.size;
                }

                if (totalSize > maxSizeBytes) {
                    isValid = false;
                    showFieldError(fileInput, `Total file size exceeds maximum allowed size of ${maxSizeMB} MB`, 'client-error');
                }
            }

            if (!isValid) {
                e.preventDefault();
                // Scroll to first error
                const firstError = document.querySelector('.client-error-message');
                if (firstError) {
                    firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    // Add new product line
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-product-line') || e.target.parentElement.classList.contains('add-product-line')) {
            e.preventDefault();

            const container = document.getElementById('product-lines-container');
            const newRow = document.createElement('div');
            newRow.className = 'product-line-row row mb-2';
            newRow.innerHTML =
                '<div class="col-md-8">' +
                    '<input type="text" name="product_description_' + lineCounter + '" placeholder="Product Description" class="form-control"/>' +
                '</div>' +
                '<div class="col-md-3">' +
                    '<input type="number" name="product_quantity_' + lineCounter + '" placeholder="Quantity" class="form-control" step="0.01" min="0.01"/>' +
                '</div>' +
                '<div class="col-md-1">' +
                    '<button type="button" class="btn btn-danger btn-sm remove-product-line">' +
                        '<i class="fa fa-minus"></i>' +
                    '</button>' +
                '</div>';

            container.appendChild(newRow);
            lineCounter++;

            // Focus on the new description field
            const newDescInput = newRow.querySelector('input[type="text"]');
            if (newDescInput) {
                newDescInput.focus();
            }
        }

        // Remove product line
        if (e.target.classList.contains('remove-product-line') || e.target.parentElement.classList.contains('remove-product-line')) {
            e.preventDefault();
            const row = e.target.closest('.product-line-row');
            if (document.querySelectorAll('.product-line-row').length > 1) {
                row.remove();
            } else {
                showAlert('warning', 'At least one product line is required');
            }
        }
    });

    // Auto-update team when collaborator changes
    const collaboratorSelect = document.getElementById('collaborator_id');
    if (collaboratorSelect) {
        collaboratorSelect.addEventListener('change', function() {
            // Clear any existing errors
            clearFieldError(this);
        });
    }

    // Quantity validation for product lines
    document.addEventListener('input', function(e) {
        if (e.target.name && e.target.name.startsWith('product_quantity_')) {
            const value = parseFloat(e.target.value);
            if (e.target.value && value <= 0) {
                showFieldError(e.target, 'Quantity must be greater than zero', 'client-error');
            } else {
                clearFieldError(e.target);
            }
        }
    });

    // No custom date-range parsing required; template uses native date inputs

    // File size validation and multi-select handling
    const fileInput = document.getElementById('attachments');
    // Internal array to store selected File objects across multiple select dialogs
    let selectedFilesArr = [];
    if (fileInput) {
        // When user picks files, append them to selectedFilesArr
        fileInput.addEventListener('change', function() {
            addFiles(this.files);
        });
        // also listen to input event in some browsers
        fileInput.addEventListener('input', function() {
            addFiles(this.files);
        });
    }

    // Render attachments list and summary when files change
    if (fileInput) {
        const attachmentsList = document.querySelector('.attachments-list');
        const attachmentsSummary = document.querySelector('.attachments-summary');
        const attachmentsRemaining = document.querySelector('.attachments-remaining');
        const attachmentsMaxEl = document.querySelector('.attachments-max');
        const maxSizeAttr = fileInput.dataset.maxSize || '10';

        // Add files from a FileList to the internal array (avoiding duplicates)
        function addFiles(fileList) {
            if (!fileList || fileList.length === 0) {
                // still render to update summary
                renderAttachments(selectedFilesArr);
                return;
            }

            Array.from(fileList).forEach(file => {
                const key = `${file.name}|${file.size}|${file.lastModified}`;
                const exists = selectedFilesArr.some(f => `${f.name}|${f.size}|${f.lastModified}` === key);
                if (!exists) selectedFilesArr.push(file);
            });

            // Sync to actual file input so the form posts the selected files
            updateInputFiles();
            renderAttachments(selectedFilesArr);
            validateFileSize(fileInput);
        }

        function updateInputFiles() {
            try {
                const dataTransfer = new DataTransfer();
                selectedFilesArr.forEach(f => dataTransfer.items.add(f));
                fileInput.files = dataTransfer.files;
            } catch (err) {
                // Fallback: some older browsers may not allow writing fileInput.files
                // In that case the UI will still show the list, but the upload may not include files.
                console.warn('Could not update file input programmatically:', err);
            }
        }

        // Remove file by index in selectedFilesArr
        function removeFileByIndex(idx) {
            if (idx < 0 || idx >= selectedFilesArr.length) return;
            selectedFilesArr.splice(idx, 1);
            updateInputFiles();
            renderAttachments(selectedFilesArr);
            validateFileSize(fileInput);
        }

        // Click handler for remove buttons in the attachments list
        if (attachmentsList) {
            attachmentsList.addEventListener('click', function(e) {
                if (e.target && e.target.classList.contains('remove-attachment')) {
                    const idx = parseInt(e.target.dataset.index, 10);
                    removeFileByIndex(idx);
                }
            });
        }

        function renderAttachments(fileArray) {
            if (!attachmentsList) return;
            attachmentsList.innerHTML = '';
            let totalBytes = 0;
            fileArray.forEach((file, index) => {
                totalBytes += file.size;
                const li = document.createElement('li');
                li.innerHTML = `<span title="${file.name}">${file.name}</span> — <small class="text-muted">${formatBytes(file.size)}</small> <button type="button" class="btn btn-link btn-sm remove-attachment" data-index="${index}" aria-label="Remove">&times;</button>`;
                attachmentsList.appendChild(li);
            });

            const maxMB = parseFloat(maxSizeAttr);
            const usedMB = (totalBytes / (1024 * 1024));
            const remainingMB = Math.max(0, maxMB - usedMB);

            if (attachmentsSummary) {
                attachmentsSummary.innerHTML = `${usedMB.toFixed(2)} MB of <span class="attachments-max">${maxMB}</span> MB used. <span class="attachments-remaining">${remainingMB.toFixed(2)} MB</span> remaining.`;
                // color the summary if near or over limit
                if (usedMB > maxMB) {
                    attachmentsSummary.style.color = '#dc3545';
                } else if (usedMB > maxMB * 0.8) {
                    attachmentsSummary.style.color = '#ffc107';
                } else {
                    attachmentsSummary.style.color = '';
                }
            }
        }

        // initial render to set summary even if no files selected
        // if the file input already has files (e.g., preserved), seed selectedFilesArr
        if (fileInput.files && fileInput.files.length > 0) {
            addFiles(fileInput.files);
        } else {
            renderAttachments([]);
        }
    }

    // Initialize preserved form data
    function initializeFormData() {
        // Count existing product lines and update counter
        const existingLines = document.querySelectorAll('input[name^="product_description_"]');
        existingLines.forEach(input => {
            const match = input.name.match(/product_description_(\d+)/);
            if (match) {
                const index = parseInt(match[1]);
                lineCounter = Math.max(lineCounter, index + 1);
            }
        });
    }

    // Helper functions
    function showFieldError(field, message, className = 'error-message') {
        // Determine where to place the error: for input-like fields place next to the field,
        // for container elements (divs) place the error inside the container.
        const target = (field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement) ? field.parentNode : field;
        if (!target) return;

        clearFieldError(field);
        const errorDiv = document.createElement('div');
        // Always include the canonical 'client-error-message' class so we can reliably find/remove it
        errorDiv.className = `${className} client-error-message invalid-feedback d-block text-danger mt-1`;
        errorDiv.textContent = message;
        target.appendChild(errorDiv);

        // Add invalid state to input-like fields only
        if (field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement) {
            field.classList.add('is-invalid');
        }
    }

    function clearFieldError(field) {
        const target = (field instanceof HTMLInputElement || field instanceof HTMLSelectElement || field instanceof HTMLTextAreaElement) ? field.parentNode : field;
        if (!target) return;

        // Remove only our client-side error messages
        const existingErrors = target.querySelectorAll('.client-error-message');
        existingErrors.forEach(error => error.remove());

        // Only remove is-invalid if there are no server-side errors remaining
        // Server-side errors are marked with 'invalid-feedback' but not our 'client-error-message'
        const serverErrors = target.querySelectorAll('.invalid-feedback:not(.client-error-message)');
        if (serverErrors.length === 0) {
            // Remove is-invalid from any input element inside the target
            const inputs = target.querySelectorAll('input, select, textarea');
            inputs.forEach(inp => inp.classList.remove('is-invalid'));
        }
    }
    
    function validateFileSize(fileInput) {
        const maxSizeMB = parseInt(fileInput.dataset.maxSize || '10');
        const maxSizeBytes = maxSizeMB * 1024 * 1024;
        let totalSize = 0;

        for (let file of fileInput.files) {
            totalSize += file.size;
        }

        // Update attachments UI if present
        const attachmentsList = document.querySelector('.attachments-list');
        if (attachmentsList) {
            // render handled by renderAttachments in the change handler
        }

        if (totalSize > maxSizeBytes) {
            showFieldError(fileInput, `Total file size exceeds maximum allowed size of ${maxSizeMB} MB`, 'client-error');
        } else {
            clearFieldError(fileInput);
        }
    }

    // Helper to format bytes into human-readable string
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    // Initialize approvers widget
    function initializeApproversWidget() {
        const approversInput = document.getElementById('approvers');
        const approversContainer = document.querySelector('.approvers-container');
        const tagsContainer = document.querySelector('.approvers-tags');
        const dropdown = document.querySelector('.approvers-dropdown');
        
        if (!approversInput || !approversContainer) return;
        
        // Load available approvers
        loadApprovers();
        
        // Handle input events to show dropdown and filter
        approversInput.addEventListener('click', showDropdown);
        approversInput.addEventListener('focus', showDropdown);
        approversInput.addEventListener('input', handleInputChange);
        approversInput.addEventListener('keydown', handleKeydown);
        
        // Hide dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!approversContainer.contains(e.target)) {
                hideDropdown();
            }
        });
        
        // Initialize from preserved values
        const hiddenApproversInput = document.querySelector('input[name="approver_ids"]');
        if (hiddenApproversInput && hiddenApproversInput.value) {
            const approverIds = hiddenApproversInput.value.split(',');
            approverIds.forEach(id => {
                if (id.trim()) {
                    addApproverTag(id.trim());
                }
            });
        }
    }
    
    function loadApprovers() {
        // Get approvers data from the template
        const approversData = document.querySelector('#approvers-data');
        if (approversData) {
            window.availableApprovers = JSON.parse(approversData.textContent);
        } else {
            window.availableApprovers = [];
        }
    }

    /* Collaborator widget */
    function initializeCollaboratorWidget() {
        const input = document.getElementById('collaborator_id_widget');
        const dropdown = document.querySelector('.collaborator-dropdown');
        const hiddenInput = document.getElementById('collaborator_id');
        if (!input || !dropdown || !hiddenInput) return;

        // Load employees
        const employeesData = document.querySelector('#employees-data');
        window.availableEmployees = employeesData ? JSON.parse(employeesData.textContent) : [];

        // Prefill display if hidden has a value
        if (hiddenInput.value) {
            const emp = window.availableEmployees.find(e => e.id && e.id.toString() === hiddenInput.value.toString());
            if (emp) {
                input.value = emp.name;
            }
        }

        input.addEventListener('input', function() {
            showCollaboratorDropdown();
            filterEmployees();
        });
        input.addEventListener('focus', function() {
            showCollaboratorDropdown();
            filterEmployees();
        });
        input.addEventListener('keydown', function(e) {
            const options = dropdown.querySelectorAll('.collaborator-option:not(.text-muted)');
            let selectedIndex = -1;
            options.forEach((opt, idx) => { if (opt.classList.contains('highlighted')) selectedIndex = idx; });
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    if (selectedIndex < options.length - 1) {
                        if (selectedIndex >= 0) options[selectedIndex].classList.remove('highlighted');
                        selectedIndex++;
                        options[selectedIndex].classList.add('highlighted');
                    }
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    if (selectedIndex > 0) {
                        options[selectedIndex].classList.remove('highlighted');
                        selectedIndex--;
                        options[selectedIndex].classList.add('highlighted');
                    }
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (selectedIndex >= 0 && options[selectedIndex]) {
                        const empId = options[selectedIndex].dataset.id;
                        const emp = window.availableEmployees.find(e => e.id && e.id.toString() === empId);
                        if (emp) selectCollaborator(emp);
                    }
                    break;
                case 'Escape':
                    hideCollaboratorDropdown();
                    break;
            }
        });

        document.addEventListener('click', function(e) {
            const container = input.closest('.collaborator-container');
            if (!container.contains(e.target)) hideCollaboratorDropdown();
        });
    }

    function showCollaboratorDropdown() {
        const dropdown = document.querySelector('.collaborator-dropdown');
        if (dropdown) {
            dropdown.style.display = 'block';
            filterEmployees();
        }
    }

    function hideCollaboratorDropdown() {
        const dropdown = document.querySelector('.collaborator-dropdown');
        if (dropdown) dropdown.style.display = 'none';
    }

    function filterEmployees() {
        const input = document.getElementById('collaborator_id_widget');
        const dropdown = document.querySelector('.collaborator-dropdown');
        const searchTerm = input.value.toLowerCase();
        dropdown.innerHTML = '';
        const filtered = window.availableEmployees.filter(emp => {
            return searchTerm === '' || emp.name.toLowerCase().includes(searchTerm) || (emp.email || '').toLowerCase().includes(searchTerm);
        });

        if (filtered.length === 0) {
            const no = document.createElement('div');
            no.className = 'collaborator-option text-muted';
            no.textContent = searchTerm ? 'No employees found' : 'No employees available';
            dropdown.appendChild(no);
        } else {
            filtered.forEach(emp => {
                const opt = document.createElement('div');
                opt.className = 'collaborator-option';
                opt.dataset.id = emp.id;
                opt.innerHTML = `<strong>${emp.name}</strong><small class="text-muted d-block">${emp.email || ''}</small>`;
                opt.addEventListener('mouseenter', () => {
                    dropdown.querySelectorAll('.collaborator-option').forEach(o => o.classList.remove('highlighted'));
                    opt.classList.add('highlighted');
                });
                opt.addEventListener('click', () => selectCollaborator(emp));
                dropdown.appendChild(opt);
            });
        }
    }

    function selectCollaborator(emp) {
        const input = document.getElementById('collaborator_id_widget');
        const hidden = document.getElementById('collaborator_id');
        if (!input || !hidden) return;
        input.value = emp.name;
        hidden.value = emp.id;
        hideCollaboratorDropdown();
        // Clear any previous client-side errors for collaborator
        clearFieldError(document.querySelector('.collaborator-container'));
    }

    function showDropdown() {
        const dropdown = document.querySelector('.approvers-dropdown');
        if (dropdown) {
            dropdown.style.display = 'block';
            filterApprovers();
        }
    }

    function hideDropdown() {
        const dropdown = document.querySelector('.approvers-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }
    
    function handleInputChange() {
        showDropdown();
        filterApprovers();
    }
    
    function handleKeydown(e) {
        const dropdown = document.querySelector('.approvers-dropdown');
        if (!dropdown || dropdown.style.display === 'none') return;
        
        const options = dropdown.querySelectorAll('.approver-option:not(.text-muted)');
        let selectedIndex = -1;
        
        // Find currently highlighted option
        options.forEach((option, index) => {
            if (option.classList.contains('highlighted')) {
                selectedIndex = index;
            }
        });
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                if (selectedIndex < options.length - 1) {
                    if (selectedIndex >= 0) options[selectedIndex].classList.remove('highlighted');
                    selectedIndex++;
                    options[selectedIndex].classList.add('highlighted');
                }
                break;
            case 'ArrowUp':
                e.preventDefault();
                if (selectedIndex > 0) {
                    options[selectedIndex].classList.remove('highlighted');
                    selectedIndex--;
                    options[selectedIndex].classList.add('highlighted');
                }
                break;
            case 'Enter':
                e.preventDefault();
                if (selectedIndex >= 0 && options[selectedIndex]) {
                    const approverId = options[selectedIndex].dataset.id;
                    const approver = window.availableApprovers.find(a => a.id.toString() === approverId);
                    if (approver) {
                        selectApprover(approver);
                    }
                }
                break;
            case 'Escape':
                hideDropdown();
                break;
        }
    }
    
    function filterApprovers() {
        const input = document.getElementById('approvers');
        const dropdown = document.querySelector('.approvers-dropdown');
        const searchTerm = input.value.toLowerCase();
        
        if (!dropdown || !window.availableApprovers) return;
        
        dropdown.innerHTML = '';
        
        const filteredApprovers = window.availableApprovers.filter(approver => {
            const isNotSelected = !selectedApprovers.has(approver.id.toString());
            const matchesSearch = searchTerm === '' || 
                                approver.name.toLowerCase().includes(searchTerm) || 
                                approver.email.toLowerCase().includes(searchTerm);
            return isNotSelected && matchesSearch;
        });
        
        if (filteredApprovers.length === 0) {
            const noResults = document.createElement('div');
            noResults.className = 'approver-option text-muted';
            noResults.textContent = searchTerm ? 'No approvers found' : 'No more approvers available';
            dropdown.appendChild(noResults);
        } else {
            filteredApprovers.forEach(approver => {
                const option = document.createElement('div');
                option.className = 'approver-option';
                option.dataset.id = approver.id;
                option.innerHTML = `
                    <strong>${approver.name}</strong>
                    <small class="text-muted d-block">${approver.email}</small>
                `;
                
                // Add hover effect
                option.addEventListener('mouseenter', () => {
                    dropdown.querySelectorAll('.approver-option').forEach(opt => {
                        opt.classList.remove('highlighted');
                    });
                    option.classList.add('highlighted');
                });
                
                option.addEventListener('click', () => selectApprover(approver));
                dropdown.appendChild(option);
            });
        }
    }
    
    function selectApprover(approver) {
        if (!selectedApprovers.has(approver.id.toString())) {
            selectedApprovers.add(approver.id.toString());
            addApproverTag(approver.id.toString(), approver.name);
            updateHiddenInput();
            
            // Clear input and refresh dropdown
            const input = document.getElementById('approvers');
            input.value = '';
            input.focus(); // Keep focus for more selections
            filterApprovers(); // Refresh to remove selected approver
        }
    }
    
    function addApproverTag(approverId, approverName = null) {
        const tagsContainer = document.querySelector('.approvers-tags');
        
        // If name not provided, find it in available approvers
        if (!approverName && window.availableApprovers) {
            const approver = window.availableApprovers.find(a => a.id.toString() === approverId);
            approverName = approver ? approver.name : `Approver ${approverId}`;
        }
        
        const tag = document.createElement('span');
        tag.className = 'approver-tag';
        tag.dataset.id = approverId;
        tag.innerHTML = `
            ${approverName || `Approver ${approverId}`}
            <span class="remove-approver" data-id="${approverId}">&times;</span>
        `;
        
        // Add remove functionality
        tag.querySelector('.remove-approver').addEventListener('click', () => {
            removeApprover(approverId);
        });
        
        tagsContainer.appendChild(tag);
        selectedApprovers.add(approverId);
    }
    
    function removeApprover(approverId) {
        selectedApprovers.delete(approverId);
        const tag = document.querySelector(`.approver-tag[data-id="${approverId}"]`);
        if (tag) {
            tag.remove();
        }
        updateHiddenInput();
    }
    
    function updateHiddenInput() {
        const hiddenInput = document.querySelector('input[name="approver_ids"]');
        if (hiddenInput) {
            hiddenInput.value = Array.from(selectedApprovers).join(',');
        }
    }
});