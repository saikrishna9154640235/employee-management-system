// dashboard.js - Wired to backend APIs

let attendanceLoggedIn = typeof ATTENDANCE_LOGGED_IN !== 'undefined' ? ATTENDANCE_LOGGED_IN : false;
let adminAttendanceLoggedIn = false;

/* Attendance - calls backend, saves login/logout times to DB */
function toggleAttendance() {
    const status = document.getElementById("status");
    const btn = document.getElementById("attendanceBtn");
    const timeDisplay = document.getElementById("time-display");
    const isCurrentlyLoggedIn = attendanceLoggedIn;
    const action = isCurrentlyLoggedIn ? "logout" : "login";

    const formData = new FormData();
    formData.append("action", action);

    fetch("/attendance", {
        method: "POST",
        body: formData,
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.success) {
                alert(data.error || "Failed to mark attendance");
                return;
            }

            attendanceLoggedIn = action === "login" && !data.logout_time;
            status.innerText = attendanceLoggedIn ? "Logged In" : "Not Logged In";
            status.style.color = attendanceLoggedIn ? "green" : "";
            btn.innerText = attendanceLoggedIn ? "Logout" : "Login";
            btn.classList.toggle("danger", attendanceLoggedIn);
            if (timeDisplay && data.login_time) {
                const logoutStr = data.logout_time ? ` | Logout: ${data.logout_time}` : " | Logout: -";
                timeDisplay.textContent = `Login: ${data.login_time}${logoutStr}`;
            }
        })
        .catch((err) => alert("Failed to mark attendance"));
}

function toggleAdminAttendance() {
    const status = document.getElementById("admin-status");
    const btn = document.getElementById("adminAttendanceBtn");
    const timeDisplay = document.getElementById("admin-time-display");
    const isCurrentlyLoggedIn = adminAttendanceLoggedIn;
    const action = isCurrentlyLoggedIn ? "logout" : "login";

    const formData = new FormData();
    formData.append("action", action);

    fetch("/attendance", {
        method: "POST",
        body: formData,
    })
        .then((r) => r.json())
        .then((data) => {
            if (!data.success) {
                alert(data.error || "Failed to mark attendance");
                return;
            }

            adminAttendanceLoggedIn = action === "login" && !data.logout_time;
            status.innerText = adminAttendanceLoggedIn ? "Logged In" : "Not Logged In";
            status.style.color = adminAttendanceLoggedIn ? "green" : "";
            btn.innerText = adminAttendanceLoggedIn ? "Logout" : "Login";
            btn.classList.toggle("danger", adminAttendanceLoggedIn);
            if (timeDisplay && data.login_time) {
                const logoutStr = data.logout_time ? ` | Logout: ${data.logout_time}` : " | Logout: -";
                timeDisplay.textContent = `Login: ${data.login_time}${logoutStr}`;
            }
        })
        .catch((err) => alert("Failed to mark attendance"));
}

/* Profile image upload - saves to backend */
function uploadProfileImage(event) {
    const file = event.target.files[0];
    if (!file) return;

    const img = document.getElementById("profileImage");
    img.src = URL.createObjectURL(file);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("profilePic", file);

    fetch("/upload_profile_image", {
        method: "POST",
        body: formData,
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.success && data.url) {
                img.src = data.url;
            } else {
                alert(data.error || "Upload failed");
            }
        })
        .catch((err) => alert("Upload failed"));
}

function previewImage(event) {
    const img = document.getElementById("profileImage");
    if (img && event.target.files[0]) {
        img.src = URL.createObjectURL(event.target.files[0]);
    }
}

/* Apply Leave - calls backend */
function applyLeave(event) {
    event.preventDefault();

    const fromDate = document.getElementById("fromDate").value;
    const toDate = document.getElementById("toDate").value;
    const leaveTypeEl = document.getElementById("leaveType");
    const leaveType = leaveTypeEl ? leaveTypeEl.value : "casual";
    const reason = document.getElementById("reason").value;

    if (!fromDate || !toDate) {
        alert("Please select from and to dates");
        return;
    }
    if (fromDate > toDate) {
        alert("From date cannot be after to date");
        return;
    }

    const formData = new FormData();
    formData.append("fromDate", fromDate);
    formData.append("toDate", toDate);
    formData.append("leaveType", leaveType);
    formData.append("reason", reason);

    fetch("/apply_leave", {
        method: "POST",
        body: formData,
    })
        .then((r) => r.json())
        .then((data) => {
            if (data.success) {
                alert("Leave applied successfully!");
                document.getElementById("leaveForm").reset();
                location.reload();
            } else {
                alert(data.error || "Failed to apply leave");
            }
        })
        .catch((err) => alert("Failed to apply leave"));
}

/* Calendar - Present / Absent / Weekend */
let currentMonth = new Date().getMonth();
let currentYear = new Date().getFullYear();
const monthNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];

async function generateCalendar(calendarId) {
    const calendar = document.getElementById(calendarId);
    if (!calendar) return;

    const month = currentMonth + 1;
    const year = currentYear;
    let attendanceData = {};

    try {
        const res = await fetch(`/api/attendance/${month}/${year}`);
        if (res.ok) {
            const data = await res.json();
            attendanceData = data.attendance || {};
        }
    } catch (e) {
        console.warn("Could not fetch attendance for calendar", e);
    }

    calendar.innerHTML = `
        <div class="calendar-header">
            <button class="calendar-nav" onclick="changeMonth('${calendarId}', -1)">‹</button>
            <div class="calendar-title">${monthNames[currentMonth]} ${currentYear}</div>
            <button class="calendar-nav" onclick="changeMonth('${calendarId}', 1)">›</button>
        </div>
        <div class="calendar-grid">
            <div class="day-header">Sun</div><div class="day-header">Mon</div><div class="day-header">Tue</div>
            <div class="day-header">Wed</div><div class="day-header">Thu</div><div class="day-header">Fri</div><div class="day-header">Sat</div>
        </div>
        <div class="calendar-grid" id="${calendarId}-days"></div>
    `;

    const daysContainer = document.getElementById(`${calendarId}-days`);
    const firstDay = new Date(currentYear, currentMonth, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();

    const today = new Date();

    for (let i = 0; i < firstDay; i++) {
        daysContainer.innerHTML += '<div class="day-cell day-empty"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const cell = document.createElement('div');
        const cellDate = new Date(currentYear, currentMonth, day);
        const dayOfWeek = cellDate.getDay();
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

        const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
        const att = attendanceData[dateStr];
        const isPresent = att && att.status === 'present';

        if (isWeekend) {
            cell.className = 'day-cell day-weekend';
            cell.title = 'Weekend';
            cell.innerHTML = `<span class="day-num">${day}</span><span class="day-mark">W</span>`;
        } else if (isPresent) {
            cell.className = 'day-cell day-present';
            cell.title = `Present${att.login_time ? ' - Login: ' + att.login_time : ''}${att.logout_time ? ', Logout: ' + att.logout_time : ''}`;
            cell.innerHTML = `<span class="day-num">${day}</span><span class="day-mark">P</span>`;
        } else {
            cell.className = 'day-cell day-absent';
            cell.title = 'Absent';
            cell.innerHTML = `<span class="day-num">${day}</span><span class="day-mark">A</span>`;
        }

        if (cellDate.toDateString() === today.toDateString()) {
            cell.classList.add('today');
        }

        daysContainer.appendChild(cell);
    }
}

function changeMonth(calendarId, direction) {
    if (direction === 1) {
        currentMonth++;
        if (currentMonth > 11) { currentMonth = 0; currentYear++; }
    } else {
        currentMonth--;
        if (currentMonth < 0) { currentMonth = 11; currentYear--; }
    }
    generateCalendar(calendarId);
}

window.onload = function() {
    setTimeout(() => {
        const empCal = document.getElementById('employeeCalendar');
        const adminCal = document.getElementById('adminCalendar');
        if (empCal) generateCalendar('employeeCalendar');
        if (adminCal) generateCalendar('adminCalendar');
    }, 100);
};
