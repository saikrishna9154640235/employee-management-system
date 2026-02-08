// login.js - Database Simulation for Testing
const users = [
    { id: 'ADMIN001', username: 'ADMIN001', email: 'admin@company.com', password: 'admin123', role: 'admin' },
    { id: 'EMP001', username: 'EMP001', email: 'john@company.com', password: 'pass123', role: 'employee' },
    { id: 'EMP002', username: 'EMP002', email: 'priya@company.com', password: 'pass123', role: 'employee' }
];

function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username')?.value || 
                     document.querySelector('input[type="text"]')?.value;
    const password = document.getElementById('password')?.value || 
                     document.querySelector('input[type="password"]')?.value;
    
    const user = users.find(u => 
        (u.username === username || u.email === username) && 
        u.password === password
    );
    
    if (user) {
        // Save user session
        localStorage.setItem('currentUser', JSON.stringify(user));
        console.log('✅ Login successful:', user);
        
        // Redirect based on role
        if (user.role === 'admin') {
            window.location.href = 'admin_dashboard.html';
        } else {
            window.location.href = 'employee_dashboard.html';
        }
    } else {
        alert('❌ Invalid username or password');
        document.querySelector('input[type="text"], input[type="email"]').focus();
    }
}

function handleForgotPassword(event) {
    event.preventDefault();
    alert('🔄 Password reset email sent! (Demo)');
}

// Initialize when page loads
// Forms with method="POST" submit to Flask - don't intercept those
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form');
    if (loginForm && loginForm.getAttribute('method')?.toUpperCase() === 'POST') {
        return; // Let Flask backend handle login
    }
    if (loginForm && !loginForm.hasAttribute('onsubmit')) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Auto-focus username field
    const usernameField = document.querySelector('input[type="text"], input[type="email"]');
    if (usernameField) usernameField.focus();
});



// Profile Picture Upload (Both Dashboards)
function initProfileUpload() {
    // Employee Dashboard
    const profileUpload = document.getElementById('profileUpload');
    const profilePic = document.getElementById('profilePic');
    const removePhoto = document.getElementById('removePhoto');
    
    if (profileUpload && profilePic) {
        // Click image to upload
        profilePic.addEventListener('click', () => profileUpload.click());
        
        // Upload file
        profileUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/') && file.size < 2000000) { // 2MB limit
                const reader = new FileReader();
                reader.onload = function(e) {
                    profilePic.src = e.target.result;
                    profilePic.classList.add('has-photo');
                    removePhoto.style.display = 'block';
                    saveProfilePic(e.target.result);
                };
                reader.readAsDataURL(file);
            } else {
                alert('Please select an image under 2MB');
            }
        });
        
        // Remove photo
        if (removePhoto) {
            removePhoto.addEventListener('click', function(e) {
                e.stopPropagation();
                profilePic.src = 'https://via.placeholder.com/80x80/3b82f6/ffffff?text=👤';
                profilePic.classList.remove('has-photo');
                this.style.display = 'none';
                localStorage.removeItem('profilePic');
            });
        }
    }
    
    // Admin Dashboard (same logic)
    const adminProfileUpload = document.getElementById('adminProfileUpload');
    const adminProfilePic = document.getElementById('adminProfilePic');
    
    if (adminProfileUpload && adminProfilePic) {
        adminProfilePic.addEventListener('click', () => adminProfileUpload.click());
        adminProfileUpload.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file && file.type.startsWith('image/') && file.size < 2000000) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    adminProfilePic.src = e.target.result;
                    saveProfilePic(e.target.result, 'admin');
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

function saveProfilePic(imageData, type = 'employee') {
    localStorage.setItem(`profilePic_${type}`, imageData);
}

// Load saved profile pic on page load
function loadProfilePic() {
    const savedPic = localStorage.getItem('profilePic');
    const profilePic = document.getElementById('profilePic');
    if (savedPic && profilePic) {
        profilePic.src = savedPic;
        document.getElementById('removePhoto').style.display = 'block';
    }
    
    const adminSavedPic = localStorage.getItem('profilePic_admin');
    const adminPic = document.getElementById('adminProfilePic');
    if (adminSavedPic && adminPic) {
        adminPic.src = adminPic.src;
    }
}

// Initialize everything
document.addEventListener('DOMContentLoaded', function() {
    initProfileUpload();
    loadProfilePic();
    // Your existing stats + calendar code...
});
