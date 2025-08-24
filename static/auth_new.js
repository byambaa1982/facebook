/* Authentication JavaScript Functions for Hamburger Menu */

// Global variables for forms and modal
let currentForm = null;
let authModal = null;

// Initialize authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    setupAuthModal();
    checkAuthStatus();
});

// Setup authentication modal
function setupAuthModal() {
    // Create auth modal
    authModal = document.createElement('div');
    authModal.id = 'auth-modal';
    authModal.className = 'modal';
    authModal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="hideAuthModal()">&times;</span>
            <div id="modal-body">
                <!-- Form content will be inserted here -->
            </div>
        </div>
    `;
    
    // Add modal styles if not already present
    if (!document.getElementById('auth-modal-styles')) {
        const style = document.createElement('style');
        style.id = 'auth-modal-styles';
        style.textContent = `
            .modal {
                display: none;
                position: fixed;
                z-index: 10000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.5);
                animation: fadeIn 0.3s ease;
            }
            
            .modal-content {
                background-color: white;
                margin: 10% auto;
                padding: 30px;
                border-radius: 12px;
                width: 90%;
                max-width: 400px;
                position: relative;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                animation: slideIn 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideIn {
                from { transform: translateY(-50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            .close {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                position: absolute;
                right: 15px;
                top: 10px;
                cursor: pointer;
            }
            
            .close:hover,
            .close:focus {
                color: #000;
                text-decoration: none;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                font-weight: 500;
                color: #333;
            }
            
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e1e5e9;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
                box-sizing: border-box;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: #1877f2;
            }
            
            .btn {
                padding: 12px 24px !important;
                border: none !important;
                border-radius: 8px !important;
                font-size: 16px !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                transition: all 0.3s !important;
                margin: 5px !important;
                text-decoration: none !important;
                display: inline-block !important;
                background: #1877f2 !important;
                color: white !important;
            }
            
            .btn:hover {
                background: #166fe5 !important;
                transform: translateY(-2px) !important;
            }
            
            .btn-secondary {
                background: #6c757d !important;
                color: white !important;
            }
            
            .btn-secondary:hover {
                background: #5a6268 !important;
            }
            
            .error-message {
                color: #dc3545;
                margin-top: 10px;
                font-size: 14px;
            }
            
            .success-message {
                color: #28a745;
                margin-top: 10px;
                font-size: 14px;
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(authModal);
    
    // Close modal when clicking outside
    authModal.onclick = function(event) {
        if (event.target === authModal) {
            hideAuthModal();
        }
    }
}

// Check if user is authenticated and update hamburger menu
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/user/status');
        const data = await response.json();
        
        if (data.logged_in) {
            showUserInfo(data.user);
        } else {
            showLoginOptions();
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
        showLoginOptions();
    }
}

// Update hamburger menu for logged-in user
function showUserInfo(user) {
    const userStatus = document.getElementById('user-status');
    const authLinks = document.getElementById('auth-links');
    
    if (userStatus) {
        userStatus.textContent = `Welcome, ${user.username}!`;
    }
    
    if (authLinks) {
        authLinks.innerHTML = `
            <a href="#" onclick="logout()" class="menu-item">Logout</a>
        `;
    }
}

// Update hamburger menu for guest user
function showLoginOptions() {
    const userStatus = document.getElementById('user-status');
    const authLinks = document.getElementById('auth-links');
    
    if (userStatus) {
        userStatus.textContent = 'Not logged in';
    }
    
    if (authLinks) {
        authLinks.innerHTML = `
            <a href="#" onclick="showLoginForm()" class="menu-item">Login</a>
            <a href="#" onclick="showRegisterForm()" class="menu-item">Register</a>
        `;
    }
}

// Show login form in modal
function showLoginForm() {
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <h2 style="margin-bottom: 25px; color: #1877f2; text-align: center;">Login</h2>
        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="login-email">Email:</label>
                <input type="email" id="login-email" required>
            </div>
            <div class="form-group">
                <label for="login-password">Password:</label>
                <input type="password" id="login-password" required>
            </div>
            <div class="form-group" style="text-align: center;">
                <button type="submit" class="btn">Login</button>
                <button type="button" onclick="hideAuthModal()" class="btn btn-secondary">Cancel</button>
            </div>
        </form>
        <div id="login-message"></div>
        <p style="text-align: center; margin-top: 20px;">
            Don't have an account? <a href="#" onclick="showRegisterForm()" style="color: #1877f2;">Register here</a>
        </p>
    `;
    authModal.style.display = 'block';
    currentForm = 'login';
    
    // Close hamburger menu
    const menuDropdown = document.getElementById('menu-dropdown');
    if (menuDropdown) {
        menuDropdown.style.display = 'none';
    }
}

// Show register form in modal
function showRegisterForm() {
    const modalBody = document.getElementById('modal-body');
    modalBody.innerHTML = `
        <h2 style="margin-bottom: 25px; color: #1877f2; text-align: center;">Register</h2>
        <form onsubmit="handleRegister(event)">
            <div class="form-group">
                <label for="register-username">Username:</label>
                <input type="text" id="register-username" required>
            </div>
            <div class="form-group">
                <label for="register-email">Email:</label>
                <input type="email" id="register-email" required>
            </div>
            <div class="form-group">
                <label for="register-password">Password:</label>
                <input type="password" id="register-password" required>
            </div>
            <div class="form-group" style="text-align: center;">
                <button type="submit" class="btn">Register</button>
                <button type="button" onclick="hideAuthModal()" class="btn btn-secondary">Cancel</button>
            </div>
        </form>
        <div id="register-message"></div>
        <p style="text-align: center; margin-top: 20px;">
            Already have an account? <a href="#" onclick="showLoginForm()" style="color: #1877f2;">Login here</a>
        </p>
    `;
    authModal.style.display = 'block';
    currentForm = 'register';
    
    // Close hamburger menu
    const menuDropdown = document.getElementById('menu-dropdown');
    if (menuDropdown) {
        menuDropdown.style.display = 'none';
    }
}

// Hide authentication modal
function hideAuthModal() {
    if (authModal) {
        authModal.style.display = 'none';
    }
    currentForm = null;
}

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const messageDiv = document.getElementById('login-message');
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.innerHTML = '<div class="success-message">Login successful! Redirecting...</div>';
            setTimeout(() => {
                hideAuthModal();
                checkAuthStatus(); // Refresh auth status
            }, 1000);
        } else {
            messageDiv.innerHTML = `<div class="error-message">${data.message}</div>`;
        }
    } catch (error) {
        console.error('Login error:', error);
        messageDiv.innerHTML = '<div class="error-message">Login failed. Please try again.</div>';
    }
}

// Handle register form submission
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const messageDiv = document.getElementById('register-message');
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            messageDiv.innerHTML = '<div class="success-message">Registration successful! You can now login.</div>';
            setTimeout(() => {
                showLoginForm(); // Switch to login form
            }, 1500);
        } else {
            messageDiv.innerHTML = `<div class="error-message">${data.message}</div>`;
        }
    } catch (error) {
        console.error('Registration error:', error);
        messageDiv.innerHTML = '<div class="error-message">Registration failed. Please try again.</div>';
    }
}

// Handle logout
async function logout() {
    try {
        const response = await fetch('/api/logout', {
            method: 'POST',
        });
        
        const data = await response.json();
        
        if (data.success) {
            checkAuthStatus(); // Refresh auth status
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Close hamburger menu
    const menuDropdown = document.getElementById('menu-dropdown');
    if (menuDropdown) {
        menuDropdown.style.display = 'none';
    }
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && authModal && authModal.style.display === 'block') {
        hideAuthModal();
    }
});
