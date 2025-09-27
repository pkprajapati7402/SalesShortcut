// Dashboard JavaScript for SalesShortcut UI Client

class DashboardManager {
    constructor() {
        this.websocket = null;
        this.reconnectInterval = null;
        this.businesses = new Map();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        this.initializeWebSocket();
        this.initializeEventListeners();
        this.updateStats();
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            this.setupWebSocketHandlers();
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.scheduleReconnect();
        }
    }
    
    setupWebSocketHandlers() {
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            
            if (this.reconnectInterval) {
                clearInterval(this.reconnectInterval);
                this.reconnectInterval = null;
            }
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        };
        
        this.websocket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnection attempts reached');
            return;
        }
        
        if (this.reconnectInterval) {
            return; // Already scheduled
        }
        
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        console.log(`Scheduling reconnect in ${delay}ms`);
        
        this.reconnectInterval = setTimeout(() => {
            this.reconnectAttempts++;
            this.initializeWebSocket();
        }, delay);
    }
    
    handleWebSocketMessage(data) {
        console.log('Received WebSocket message:', data);
        console.log('Message type is:', data.type, 'Type of:', typeof data.type);
        
        switch (data.type) {
            case 'initial_state':
                this.handleInitialState(data);
                break;
            case 'business_added':
                this.handleBusinessAdded(data);
                break;
            case 'business_updated':
                this.handleBusinessUpdated(data);
                break;
            case 'process_started':
                this.handleProcessStarted(data);
                break;
            case 'lead_finding_completed':
                this.handleLeadFindingCompleted(data);
                break;
            case 'lead_finding_failed':
                this.handleLeadFindingFailed(data);
                break;
            case 'lead_finding_empty':
                this.handleLeadFindingEmpty(data);
                break;
            case 'process_finished':
                this.handleProcessFinished(data);
                break;
            case 'state_reset':
                this.handleStateReset(data);
                break;
            case 'sdr_engaged':
                this.handleSdrEngaged(data);
                break;
            case 'human_input_request':
                console.log('Matched human_input_request case!');
                this.handleHumanInputRequest(data);
                break;
            case 'human_input_response_submitted':
                this.handleHumanInputResponseSubmitted(data);
                break;
            case 'calendar_notification':
                this.handleCalendarNotification(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }
    
    handleInitialState(data) {
        console.log('Loading initial state:', data);
        
        // Clear existing businesses
        this.businesses.clear();
        
        // Load businesses
        if (data.businesses) {
            data.businesses.forEach(business => {
                this.businesses.set(business.id, business);
            });
        }
        
        // Update UI
        this.updateStats();
        this.updateAgentStatuses(data.is_running);
        
        // Don't close human input dialog on initial state - it might be legitimate state refresh
        // Only close dialog if it was just submitted (check for success message)
    }
    
    handleBusinessAdded(data) {
        console.log('Business added:', data.business);
        
        this.businesses.set(data.business.id, data.business);
        this.addBusinessCard(data.business, data.agent);
        this.updateStats();
        this.addActivityLogEntry(data.agent, `Found business: ${data.business.name}`, data.timestamp);
        this.updateAgentStatus(data.agent, true);
    }
    
    handleBusinessUpdated(data) {
        console.log('Business updated:', data.business);
        
        const oldBusiness = this.businesses.get(data.business.id);
        this.businesses.set(data.business.id, data.business);
        
        if (!oldBusiness) {
            // This is a new business, create a new card
            console.log('Creating new business card for:', data.business.name);
            this.addBusinessCard(data.business, data.agent);
        } else if (oldBusiness.status !== data.business.status) {
            // Status changed, move the card
            console.log('Moving business card due to status change:', data.business.name);
            this.moveBusinessCard(data.business, oldBusiness.status, data.business.status);
        } else {
            // Update existing card
            this.updateBusinessCard(data.business);
        }
        
        this.updateStats();
        this.addActivityLogEntry(
            data.agent, 
            `Updated ${data.business.name}: ${data.update.message}`, 
            data.timestamp
        );
        this.updateAgentStatus(data.agent, true);
    }
    
    handleProcessStarted(data) {
        console.log('Process started for city:', data.city);
        this.showLoadingOverlay();
        this.updateAgentStatus('lead_finder', true);
        this.addActivityLogEntry('system', `Started lead finding for ${data.city}`, data.timestamp);
    }
    
    handleLeadFindingCompleted(data) {
        console.log('Lead finding completed:', data);
        this.hideLoadingOverlay();
        this.updateAgentStatus('lead_finder', false);
        this.addActivityLogEntry(
            'lead_finder', 
            `Found ${data.business_count} businesses in ${data.city}`, 
            data.timestamp
        );
    }
    
    handleLeadFindingFailed(data) {
        console.log('Lead finding failed:', data);
        this.hideLoadingOverlay();
        this.updateAgentStatus('lead_finder', false);
        this.addActivityLogEntry('lead_finder', `Error: ${data.error}`, data.timestamp);
        this.showErrorToast(data.error);
    }
    
    handleLeadFindingEmpty(data) {
        console.log('Lead finding empty:', data);
        this.addActivityLogEntry('lead_finder', data.message, data.timestamp);
        // No error toast for empty results - this is normal behavior
    }
    
    handleProcessFinished(data) {
        console.log('Process finished:', data);
        // Any final cleanup can be done here
    }
    
    handleStateReset(data) {
        console.log('State reset');
        this.businesses.clear();
        this.clearAllBusinessCards();
        this.updateStats();
        this.updateAgentStatuses(false);
        this.addActivityLogEntry('system', 'Dashboard reset', data.timestamp);
    }
    
    addBusinessCard(business, agent) {
        const column = this.getColumnForStatus(business.status);
        if (!column) return;
        
        const content = column.querySelector('.column-content');
        const card = this.createBusinessCard(business);
        
        // Add with animation
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        content.appendChild(card);
        
        // Trigger animation
        requestAnimationFrame(() => {
            card.style.transition = 'all 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    }
    
    updateBusinessCard(business) {
        const existingCard = document.querySelector(`[data-business-id="${business.id}"]`);
        if (!existingCard) return;
        
        const newCard = this.createBusinessCard(business);
        existingCard.parentNode.replaceChild(newCard, existingCard);
    }
    
    moveBusinessCard(business, oldStatus, newStatus) {
        const existingCard = document.querySelector(`[data-business-id="${business.id}"]`);
        if (!existingCard) {
            // Card doesn't exist, create new one
            this.addBusinessCard(business, this.getAgentForStatus(newStatus));
            return;
        }
        
        const newColumn = this.getColumnForStatus(newStatus);
        if (!newColumn) return;
        
        const newContent = newColumn.querySelector('.column-content');
        
        // Remove from old location
        existingCard.remove();
        
        // Create new card in new location
        const newCard = this.createBusinessCard(business);
        newCard.style.opacity = '0';
        newCard.style.transform = 'translateY(20px)';
        newContent.appendChild(newCard);
        
        // Animate in
        requestAnimationFrame(() => {
            newCard.style.transition = 'all 0.3s ease';
            newCard.style.opacity = '1';
            newCard.style.transform = 'translateY(0)';
        });
    }
    
    createBusinessCard(business) {
        const card = document.createElement('div');
        const isHotLead = business.status === 'converting';
        const isMeeting = business.status === 'meeting_scheduled';
        const isClickable = business.status === 'found'; // Only "found" businesses can be sent to SDR
        
        card.className = `business-card compact ${isMeeting ? 'meeting-card' : ''} ${isHotLead ? 'hot-lead' : ''} ${isClickable ? 'clickable' : ''}`;
        card.setAttribute('data-business-id', business.id);
        
        // Add click handler for "found" status businesses
        if (isClickable) {
            card.addEventListener('click', () => {
                this.showSdrDialog(business);
            });
        }
        
        const statusText = this.getStatusText(business.status);
        // For meeting_scheduled status, use 'meeting' class to match CSS
        const statusClass = isMeeting ? 'meeting' : business.status.replace('_', '-');
        
        // Create compact notes if available
        let compactNotesHtml = '';
        if (business.notes && business.notes.length > 0) {
            const lastNote = business.notes[business.notes.length - 1];
            const truncatedNote = lastNote.length > 50 ? lastNote.substring(0, 50) + '...' : lastNote;
            const noteIcon = isMeeting ? 'fas fa-calendar-check' : 'fas fa-sticky-note';
            compactNotesHtml = `
                <div class="compact-notes">
                    <i class="${noteIcon}"></i>
                    <span>${this.escapeHtml(truncatedNote)}</span>
                </div>
            `;
        }
        
        // Create contact row
        let contactRowHtml = '';
        const contactItems = [];
        if (business.phone) {
            contactItems.push(`<div class="contact-item"><i class="fas fa-phone"></i><span>${this.escapeHtml(business.phone)}</span></div>`);
        }
        if (business.email) {
            const truncatedEmail = business.email.length > 20 ? business.email.substring(0, 20) + '...' : business.email;
            contactItems.push(`<div class="contact-item"><i class="fas fa-envelope"></i><span>${this.escapeHtml(truncatedEmail)}</span></div>`);
        }
        if (contactItems.length > 0) {
            contactRowHtml = `<div class="contact-row">${contactItems.join('')}</div>`;
        }
        
        // Create business title with icon for special statuses
        let businessTitleHtml = '';
        if (isHotLead) {
            businessTitleHtml = `
                <div class="business-title">
                    <i class="fas fa-fire hot-icon"></i>
                    <h4>${this.escapeHtml(business.name)}</h4>
                </div>
            `;
        } else if (isMeeting) {
            businessTitleHtml = `
                <div class="business-title">
                    <i class="fas fa-handshake meeting-icon"></i>
                    <h4>${this.escapeHtml(business.name)}</h4>
                </div>
            `;
        } else {
            businessTitleHtml = `<h4>${this.escapeHtml(business.name)}</h4>`;
        }
        
        // Adjust status text for compact display
        const compactStatusText = isMeeting ? 'Meeting' : statusText;
        
        card.innerHTML = `
            <div class="business-header">
                ${businessTitleHtml}
                <span class="status-badge status-${statusClass}">${compactStatusText}</span>
            </div>
            <div class="business-details">
                ${business.city ? `<div class="detail"><i class="fas fa-map-marker-alt"></i><span>${this.escapeHtml(business.city)}</span></div>` : ''}
                ${contactRowHtml}
                ${compactNotesHtml}
            </div>
        `;
        
        return card;
    }
    
    getColumnForStatus(status) {
        const statusToAgent = {
            'found': 'lead_finder',
            'contacted': 'sdr',
            'engaged': 'sdr',
            'not_interested': 'sdr',
            'no_response': 'sdr',
            'converting': 'lead_manager',
        'meeting_scheduled': 'calendar'
        };
        
        const agentType = statusToAgent[status];
        if (!agentType) return null;
        
        return document.querySelector(`[data-agent="${agentType}"]`);
    }
    
    getAgentForStatus(status) {
        const statusToAgent = {
            'found': 'lead_finder',
            'contacted': 'sdr',
            'engaged': 'sdr',
            'not_interested': 'sdr',
            'no_response': 'sdr',
            'converting': 'lead_manager',
        'meeting_scheduled': 'calendar'
        };
        
        return statusToAgent[status] || 'unknown';
    }
    
    getStatusText(status) {
        const statusTexts = {
            'found': 'Found',
            'contacted': 'Contacted',
            'engaged': 'Engaged',
            'not_interested': 'Not Interested',
            'no_response': 'No Response',
            'converting': 'Converting',
            'meeting_scheduled': 'Meeting Scheduled'
        };
        
        return statusTexts[status] || status;
    }
    
    updateStats() {
        const totalElement = document.getElementById('total-businesses');
        const engagedElement = document.getElementById('engaged-count');
        const convertingElement = document.getElementById('converting-count');
        const meetingsElement = document.getElementById('meetings-count');
        
        if (!totalElement) return;
        
        let engaged = 0;
        let converting = 0;
        let meetings = 0;
        
        this.businesses.forEach(business => {
            if (business.status === 'engaged') engaged++;
            if (business.status === 'converting') converting++;
            if (business.status === 'meeting_scheduled') meetings++;
        });
        
        this.animateCounter(totalElement, this.businesses.size);
        this.animateCounter(engagedElement, engaged);
        this.animateCounter(convertingElement, converting);
        this.animateCounter(meetingsElement, meetings);
    }
    
    animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        if (currentValue === targetValue) return;
        
        const increment = targetValue > currentValue ? 1 : -1;
        const duration = 300;
        const steps = Math.abs(targetValue - currentValue);
        const stepDuration = duration / steps;
        
        let current = currentValue;
        const timer = setInterval(() => {
            current += increment;
            element.textContent = current;
            
            if (current === targetValue) {
                clearInterval(timer);
            }
        }, stepDuration);
    }
    
    updateAgentStatus(agentType, isActive) {
        const statusElement = document.getElementById(`${agentType.replace('_', '-')}-status`);
        if (!statusElement) return;
        
        const indicator = statusElement.querySelector('.status-indicator');
        if (!indicator) return;
        
        indicator.className = `status-indicator ${isActive ? 'active' : 'idle'}`;
    }
    
    updateAgentStatuses(isRunning) {
        const agents = ['lead-finder', 'sdr', 'lead-manager', 'calendar'];
        agents.forEach(agent => {
            this.updateAgentStatus(agent.replace('-', '_'), isRunning);
        });
    }
    
    addActivityLogEntry(agent, message, timestamp) {
        const logContent = document.getElementById('activity-log');
        if (!logContent) return;
        
        const entry = document.createElement('div');
        entry.className = 'log-entry';
        entry.innerHTML = `
            <span class="log-time">${this.formatDateTime(timestamp)}</span>
            <span class="log-agent">${agent.replace('_', ' ')}</span>
            <span class="log-message">${this.escapeHtml(message)}</span>
        `;
        
        logContent.insertBefore(entry, logContent.firstChild);
        
        // Keep only last 50 entries
        const entries = logContent.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }
    }
    
    clearAllBusinessCards() {
        const contents = document.querySelectorAll('.column-content');
        contents.forEach(content => {
            content.innerHTML = '';
        });
    }
    
    showLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
    
    showErrorToast(message) {
        // Error toasts are muted - only log to console
        console.log('Error toast muted:', message);
    }
    
    updateConnectionStatus(isConnected) {
        // You can add visual feedback for connection status here
        console.log(`Connection status: ${isConnected ? 'Connected' : 'Disconnected'}`);
    }
    
    formatDateTime(dateTimeString) {
        try {
            const date = new Date(dateTimeString);
            return date.toLocaleString();
        } catch (error) {
            return dateTimeString;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    initializeEventListeners() {
        // Any additional event listeners can be added here
    }
    
    handleSdrEngaged(data) {
        console.log('SDR engaged for business:', data.business_name);
        this.addActivityLogEntry('sdr', data.message, data.timestamp);
        this.showSuccessToast(`${data.business_name} sent to SDR agent successfully!`);
        
        // Close the dialog if it's open and visible
        const dialog = document.getElementById('sdr-dialog-overlay');
        if (dialog && !dialog.classList.contains('hidden')) {
            this.closeSdrDialog();
        }
    }
    
    handleHumanInputRequest(data) {
        console.log('Received human input request:', data);
        console.log('About to show human input dialog...');
        this.addActivityLogEntry('sdr', 'Requesting human input for website creation', data.timestamp);
        
        // Show the human input modal
        showHumanInputDialog(data);
        console.log('Human input dialog show function called');
    }
    
    handleHumanInputResponseSubmitted(data) {
        console.log('Human input response submitted:', data);
        this.addActivityLogEntry('sdr', `Website URL submitted: ${data.response}`, data.timestamp);
        // Close the human input dialog if it's still open
        closeHumanInputDialog();
    }
    
    /**
     * Handle incoming calendar (meeting) notifications (meeting request stage).
     * @param {Object} data - Payload with meeting request details
     */
    handleCalendarNotification(data) {
        console.log('Received calendar notification:', data);
        this.addActivityLogEntry('calendar', data.message, data.timestamp);
        const container = document.getElementById('meeting-scheduled-content');
        if (!container) {
            console.error('Calendar column-content not found (id="meeting-scheduled-content")');
            return;
        }
        const req = data.data || {};
        const card = document.createElement('div');
        // Use the same meeting-card style as other business cards
        card.className = 'business-card compact meeting-card';
        card.setAttribute('data-business-id', `${data.business_id}-meeting`);
        const title = req.title || '';
        const desc = req.description || '';
        const start = req.start_datetime || '';
        const end = req.end_datetime || '';
        const attendees = Array.isArray(req.attendees) ? req.attendees : [];
        card.innerHTML = `
            <div class="business-header">
                <div class="business-title">
                    <i class="fas fa-handshake meeting-icon"></i>
                    <h4>${this.escapeHtml(title)}</h4>
                </div>
                <span class="status-badge status-meeting-scheduled">Meeting</span>
            </div>
            <div class="business-details">
                ${desc ? `<div class="detail"><i class="fas fa-info-circle"></i><span>${this.escapeHtml(desc)}</span></div>` : ''}
                <div class="detail"><i class="fas fa-calendar-alt"></i><span>${this.escapeHtml(this.formatDateTime(start))} - ${this.escapeHtml(this.formatDateTime(end))}</span></div>
                ${attendees.length ? `<div class="detail"><i class="fas fa-users"></i><span>${attendees.map(a => this.escapeHtml(a)).join(', ')}</span></div>` : ''}
            </div>
        `;
        container.appendChild(card);
    }
    
    showSdrDialog(business) {
        console.log('Showing SDR dialog for business:', business.name);
        
        // Get the dialog element
        const dialog = document.getElementById('sdr-dialog-overlay');
        if (!dialog) {
            console.error('SDR dialog overlay not found!');
            return;
        }
        
        // Populate business preview
        const preview = document.getElementById('business-preview');
        if (!preview) {
            console.error('Business preview element not found!');
            return;
        }
        
        preview.innerHTML = `
            <h4>${this.escapeHtml(business.name)}</h4>
            ${business.city ? `<div class="detail"><i class="fas fa-map-marker-alt"></i><span>${this.escapeHtml(business.city)}</span></div>` : ''}
            ${business.phone ? `<div class="detail"><i class="fas fa-phone"></i><span>${this.escapeHtml(business.phone)}</span></div>` : ''}
            ${business.email ? `<div class="detail"><i class="fas fa-envelope"></i><span>${this.escapeHtml(business.email)}</span></div>` : ''}
            ${business.description ? `<div class="detail"><i class="fas fa-info-circle"></i><span>${this.escapeHtml(business.description)}</span></div>` : ''}
        `;
        
        // Store the business ID for later use
        const confirmBtn = document.getElementById('confirm-sdr-btn');
        if (!confirmBtn) {
            console.error('Confirm SDR button not found!');
            return;
        }
        confirmBtn.setAttribute('data-business-id', business.id);
        
        // Show the dialog by removing the hidden class
        dialog.classList.remove('hidden');
        
        console.log('Dialog should now be visible. Current display:', dialog.style.display);
        console.log('Dialog computed style:', window.getComputedStyle(dialog).display);
        
        // Initialize phone input with masking and button state
        this.initializePhoneInput();
        this.updateSendButtonState();
        
        // Add event listener for ESC key
        document.addEventListener('keydown', this.handleDialogKeydown);
    }
    
    closeSdrDialog() {
        console.log('DashboardManager.closeSdrDialog() called');
        const dialog = document.getElementById('sdr-dialog-overlay');
        console.log('Dialog element:', dialog);
        console.log('Dialog classes before:', dialog ? dialog.className : 'dialog not found');
        
        if (dialog) {
            // Hide the dialog by adding the hidden class
            dialog.classList.add('hidden');
            console.log('Hidden class added');
            console.log('Dialog classes after:', dialog.className);
            console.log('Dialog computed style after change:', window.getComputedStyle(dialog).display);
            
            // Reset button state if it exists
            const button = document.getElementById('confirm-sdr-btn');
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-paper-plane"></i> Send to SDR';
                button.removeAttribute('data-business-id');
                console.log('Button state reset');
            }
        } else {
            console.error('Dialog element not found!');
        }
        
        // Remove event listener
        document.removeEventListener('keydown', this.handleDialogKeydown);
        console.log('Event listener removed');
    }
    
    handleDialogKeydown = (event) => {
        if (event.key === 'Escape') {
            this.closeSdrDialog();
        }
    }
    
    initializePhoneInput() {
        const phoneInput = document.getElementById('sdr-phone-input');
        if (!phoneInput) return;
        
        // Clear any existing value
        phoneInput.value = '';
        
        // Remove existing event listeners to avoid duplicates
        phoneInput.removeEventListener('input', this.handlePhoneInput);
        phoneInput.removeEventListener('blur', this.handlePhoneBlur);
        
        // Add phone number masking
        this.    handlePhoneInput = (e) => {
            let value = e.target.value.replace(/\D/g, ''); // Remove all non-digits
            let formattedValue = '';
            
            if (value.length > 0) {
                if (value.length <= 3) {
                    formattedValue = `(${value}`;
                } else if (value.length <= 6) {
                    formattedValue = `(${value.slice(0, 3)}) ${value.slice(3)}`;
                } else {
                    formattedValue = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
                }
            }
            
            e.target.value = formattedValue;
            
            // Update button state immediately
            this.updateSendButtonState();
        };
        
        // Add validation on blur
        this.handlePhoneBlur = (e) => {
            const value = e.target.value.replace(/\D/g, '');
            if (value.length !== 10) {
                e.target.setCustomValidity('Please enter a valid 10-digit US phone number');
            } else {
                e.target.setCustomValidity('');
            }
            this.updateSendButtonState();
        };
        
        phoneInput.addEventListener('input', this.handlePhoneInput);
        phoneInput.addEventListener('blur', this.handlePhoneBlur);
    }
    
    updateSendButtonState() {
        const phoneInput = document.getElementById('sdr-phone-input');
        const sendButton = document.getElementById('confirm-sdr-btn');
        const validationStatus = document.getElementById('phone-validation-status');
        const validationIcon = document.getElementById('phone-validation-icon');
        
        if (!phoneInput || !sendButton) return;
        
        const phoneValue = phoneInput.value.replace(/\D/g, '');
        // Simplified validation - just check if we have 10 digits (US phone number)
        const isValid = phoneValue.length === 10;
        
        sendButton.disabled = !isValid;
        
        if (isValid) {
            sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Send to SDR';
            phoneInput.classList.add('valid-input');
            phoneInput.classList.remove('invalid-input');
            
            if (validationStatus) {
                validationStatus.textContent = 'Valid number';
                validationStatus.className = 'validation-status valid';
            }
            
            if (validationIcon) {
                validationIcon.innerHTML = '✓';
                validationIcon.style.display = 'block';
                validationIcon.style.color = 'var(--success-color)';
            }
        } else {
            if (phoneValue.length > 0) {
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Enter Valid Phone';
                phoneInput.classList.add('invalid-input');
                phoneInput.classList.remove('valid-input');
                
                if (validationStatus) {
                    validationStatus.textContent = 'US format required (10 digits)';
                    validationStatus.className = 'validation-status invalid';
                }
                
                if (validationIcon) {
                    validationIcon.innerHTML = '✗';
                    validationIcon.style.display = 'block';
                    validationIcon.style.color = 'var(--danger-color)';
                }
            } else {
                sendButton.innerHTML = '<i class="fas fa-paper-plane"></i> Enter Phone Number';
                phoneInput.classList.remove('invalid-input');
                phoneInput.classList.remove('valid-input');
                
                if (validationStatus) {
                    validationStatus.textContent = '';
                    validationStatus.className = 'validation-status';
                }
                
                if (validationIcon) {
                    validationIcon.style.display = 'none';
                }
            }
        }
    }
    
    async confirmSendToSdr() {
        const button = document.getElementById('confirm-sdr-btn');
        const businessId = button.getAttribute('data-business-id');
        const phoneInput = document.getElementById('sdr-phone-input');
        
        // Button should already be disabled if phone is invalid, but double-check
        if (button.disabled) return;
        
        if (!businessId) {
            console.error('No business ID found');
            this.closeSdrDialog();
            return;
        }
        
        const phoneValue = phoneInput.value.replace(/\D/g, '');
        
        // Final validation (should not be needed due to real-time validation)
        if (phoneValue.length !== 10) {
            this.showErrorToast('Please enter a valid 10-digit US phone number');
            return;
        }
        
        // Disable the button and show loading
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        
        try {
            const formData = new FormData();
            formData.append('business_id', businessId);
            formData.append('user_phone', phoneValue);
            
            const response = await fetch('/send_to_sdr', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                // Handle HTTP errors
                const errorText = await response.text();
                let errorMessage = 'Failed to send to SDR agent';
                try {
                    const errorResult = JSON.parse(errorText);
                    errorMessage = errorResult.error || errorMessage;
                } catch (e) {
                    errorMessage = `Server error: ${response.status} ${response.statusText}`;
                }
                
                console.error('HTTP error sending to SDR:', errorMessage);
                this.showErrorToast(errorMessage);
                
                // Re-enable the button and close dialog
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-paper-plane"></i> Send to SDR';
                this.closeSdrDialog();
                return;
            }
            
            const result = await response.json();
            
            if (result.success) {
                console.log('Successfully sent to SDR:', result.message);
                // Close the dialog on success - WebSocket will handle success message
                this.closeSdrDialog();
            } else {
                console.error('Failed to send to SDR:', result.error);
                this.showErrorToast(result.error || 'Failed to send to SDR agent');
                
                // Re-enable the button and close dialog
                button.disabled = false;
                button.innerHTML = '<i class="fas fa-paper-plane"></i> Send to SDR';
                this.closeSdrDialog();
            }
        } catch (error) {
            console.error('Network error sending to SDR:', error);
            this.showErrorToast('Network error: Failed to communicate with server');
            
            // Re-enable the button and close dialog
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-paper-plane"></i> Send to SDR';
            this.closeSdrDialog();
        }
    }
    
    showSuccessToast(message) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 10001;
            max-width: 400px;
            font-weight: 500;
        `;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 4000);
    }
}

// Global toast function
function showToast(message, type = 'info') {
    // Mute error and warning toasts - only log to console
    if (type === 'error' || type === 'warning') {
        console.log(`${type.charAt(0).toUpperCase() + type.slice(1)} toast muted:`, message);
        return;
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let backgroundColor;
    switch(type) {
        case 'success':
            backgroundColor = '#10b981';
            break;
        default:
            backgroundColor = '#3b82f6';
    }
    
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${backgroundColor};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 10001;
        max-width: 400px;
        font-weight: 500;
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    });
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }, 4000);
}

// Global functions
function resetDashboard() {
    if (confirm('Are you sure you want to reset the dashboard and start a new search?')) {
        fetch('/reset', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    window.location.href = '/';
                } else {
                    console.error('Failed to reset dashboard');
                }
            })
            .catch(error => {
                console.error('Error resetting dashboard:', error);
            });
    }
}

// Global dialog functions
let dashboardManagerInstance = null;

function closeSdrDialog() {
    console.log('Global closeSdrDialog called');
    if (dashboardManagerInstance) {
        console.log('Calling dashboardManagerInstance.closeSdrDialog()');
        dashboardManagerInstance.closeSdrDialog();
    } else {
        console.error('dashboardManagerInstance is null!');
    }
}

function confirmSendToSdr() {
    if (dashboardManagerInstance) {
        dashboardManagerInstance.confirmSendToSdr();
    }
}

function toggleLog() {
    const logElement = document.querySelector('.activity-log');
    const toggleButton = document.querySelector('.toggle-log i');
    
    if (logElement.classList.contains('collapsed')) {
        logElement.classList.remove('collapsed');
        toggleButton.className = 'fas fa-chevron-up';
    } else {
        logElement.classList.add('collapsed');
        toggleButton.className = 'fas fa-chevron-down';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing dashboard...');
    dashboardManagerInstance = new DashboardManager();
});

// Handle page visibility changes to manage WebSocket connection
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        console.log('Page hidden, WebSocket may be paused');
    } else {
        console.log('Page visible, ensuring WebSocket is connected');
    }
});

// Human Input Modal Functions
let currentHumanInputRequest = null;

function showHumanInputDialog(requestData) {
    console.log('Showing human input dialog:', requestData);
    
    currentHumanInputRequest = requestData;
    
    // Populate the prompt
    const promptTextarea = document.getElementById('human-input-prompt');
    if (promptTextarea) {
        promptTextarea.value = requestData.prompt || '';
    }
    
    // Show the modal
    const overlay = document.getElementById('human-input-dialog-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        
        // Add fade-in animation
        overlay.style.opacity = '0';
        setTimeout(() => {
            overlay.style.opacity = '1';
        }, 10);
    }
    
    // Clear previous URL input
    const urlInput = document.getElementById('website-url-input');
    if (urlInput) {
        urlInput.value = '';
    }
    
    // Focus on URL input
    setTimeout(() => {
        if (urlInput) {
            urlInput.focus();
        }
    }, 300);
}

function closeHumanInputDialog() {
    const overlay = document.getElementById('human-input-dialog-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.style.opacity = '0';
    }
    
    currentHumanInputRequest = null;
}

function copyPromptToClipboard() {
    const promptTextarea = document.getElementById('human-input-prompt');
    if (promptTextarea) {
        promptTextarea.select();
        
        // Use modern clipboard API if available, fallback to execCommand
        if (navigator.clipboard) {
            navigator.clipboard.writeText(promptTextarea.value).then(() => {
                showToast('Prompt copied to clipboard!', 'success');
            }).catch(() => {
                // Fallback to execCommand
                document.execCommand('copy');
                showToast('Prompt copied to clipboard!', 'success');
            });
        } else {
            document.execCommand('copy');
            showToast('Prompt copied to clipboard!', 'success');
        }
    }
}

function openFirebaseStudio() {
    // Open Firebase Studio in a new tab
    window.open('https://studio.firebase.google.com/', '_blank');
}

async function submitWebsiteUrl() {
    if (!currentHumanInputRequest) {
        showToast('No active request found', 'error');
        return;
    }
    
    const urlInput = document.getElementById('website-url-input');
    const submitBtn = document.getElementById('submit-website-url-btn');
    
    if (!urlInput.value.trim()) {
        showToast('Please enter a website URL', 'error');
        urlInput.focus();
        return;
    }
    
    // Validate URL format
    try {
        new URL(urlInput.value.trim());
    } catch (e) {
        showToast('Please enter a valid URL', 'error');
        urlInput.focus();
        return;
    }
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    
    try {
        const response = await fetch(`/api/human-input/${currentHumanInputRequest.request_id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                request_id: currentHumanInputRequest.request_id,
                response: urlInput.value.trim()
            })
        });
        
        if (response.ok) {
            await response.json(); // Response received but not used
            showToast('Website URL submitted successfully!', 'success');
            // Close the human input dialog here to prevent it from reappearing if no WebSocket event arrives
            closeHumanInputDialog();
        } else {
            const error = await response.json();
            showToast(`Error: ${error.message || 'Failed to submit URL'}`, 'error');
        }
    } catch (error) {
        console.error('Error submitting website URL:', error);
        showToast('Error submitting URL. Please try again.', 'error');
    } finally {
        // Reset button state
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-check"></i> Submit URL';
    }
}

// Handle ESC key for human input modal and keyboard shortcuts
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const overlay = document.getElementById('human-input-dialog-overlay');
        if (overlay && !overlay.classList.contains('hidden')) {
            closeHumanInputDialog();
        }
    }
    
    // Keyboard shortcut: Ctrl+Shift+L to trigger Lead Manager
    if (event.ctrlKey && event.shiftKey && event.key === 'L') {
        event.preventDefault();
        console.log('🔥 Keyboard shortcut triggered: Ctrl+Shift+L - Triggering Lead Manager');
        triggerLeadManager();
    }
});

// Function to trigger lead manager agent
async function triggerLeadManager() {
    console.log('🤖 Triggering Lead Manager agent...');
    
    try {
        const response = await fetch('/trigger_lead_manager', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                trigger: 'manual',
                timestamp: new Date().toISOString()
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            let errorMessage = 'Failed to trigger Lead Manager agent';
            try {
                const errorResult = JSON.parse(errorText);
                errorMessage = errorResult.error || errorMessage;
            } catch (e) {
                errorMessage = `Server error: ${response.status} ${response.statusText}`;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        console.log('✅ Lead Manager agent triggered successfully:', result);
        showToast('Lead Manager agent triggered successfully!', 'success');
        
        // Add activity log entry
        if (window.dashboard) {
            window.dashboard.addActivityLogEntry('lead_manager', 'Agent triggered manually', new Date().toISOString());
        }
        
    } catch (error) {
        console.error('❌ Error triggering Lead Manager agent:', error);
        showToast(`Error: ${error.message}`, 'error');
    }
}

// Test function to manually trigger human input dialog
function testHumanInputDialog() {
    const testData = {
        request_id: 'test-' + Date.now(),
        prompt: 'Create a professional website for a local bakery called "Sweet Dreams Bakery". The website should include:\n\n1. A welcoming homepage with beautiful images of baked goods\n2. An about page telling the story of the bakery\n3. A menu page showcasing different products (breads, pastries, cakes)\n4. Contact information and location\n5. Online ordering capability\n6. Modern, clean design with warm colors\n7. Mobile-responsive layout\n\nThe target audience is local residents who appreciate fresh, artisanal baked goods. The tone should be warm, inviting, and family-friendly.',
        input_type: 'website_creation',
        timestamp: new Date().toISOString()
    };
    
    showHumanInputDialog(testData);
}