-- Employees Table

CREATE TABLE employees (
    id INT IDENTITY(1,1) PRIMARY KEY,
    emp_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255) NOT NULL,
    department VARCHAR(50),
    role VARCHAR(10) CHECK (role IN ('employee', 'admin')) DEFAULT 'employee',
    doj DATE,
    status VARCHAR(10) CHECK (status IN ('active', 'inactive', 'on_leave')) DEFAULT 'active',
    created_at DATETIME DEFAULT GETDATE()
);
PRINT 'Employees table created';
-- Leaves Table
CREATE TABLE leaves (
    id INT IDENTITY(1,1) PRIMARY KEY,
    emp_id VARCHAR(20),
    from_date DATE,
    to_date DATE,
    type VARCHAR(20) CHECK (type IN ('casual', 'sick', 'paid')),
    reason NVARCHAR(500),
    status VARCHAR(10) CHECK (status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    applied_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_leaves_emp FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);
PRINT 'leaves table created';

-- Attendance Table
CREATE TABLE attendance (
    id INT IDENTITY(1,1) PRIMARY KEY,
    emp_id VARCHAR(20),
    date DATE,
    status VARCHAR(10) CHECK (status IN ('present', 'absent')) DEFAULT 'absent',
    login_time DATETIME NULL,
    logout_time DATETIME NULL,
    CONSTRAINT FK_attendance_emp FOREIGN KEY (emp_id) REFERENCES employees(emp_id),
    CONSTRAINT UQ_attendance_date UNIQUE (emp_id, date)
);
PRINT 'attendance table created';

DELETE FROM attendance;
DELETE FROM leaves; 
DELETE FROM employees;
PRINT 'Cleared all data';

-- Employees (matches both dashboards)
INSERT INTO employees VALUES 
('ADMIN001', 'Hari Priya', 'admin@company.com', 'admin123', 'HR', 'admin', '2020-01-01', 'active', DEFAULT),
('EMP001', 'John Doe', 'john@company.com', 'pass123', 'Development', 'employee', '2023-01-10', 'active', DEFAULT),
('EMP002', 'Priya Sharma', 'priya@company.com', 'pass123', 'HR', 'employee', '2022-03-15', 'active', DEFAULT),
('EMP003', 'Rahul Kumar', 'rahul@company.com', 'pass123', 'Finance', 'employee', '2023-06-01', 'on_leave', DEFAULT);

-- Leaves (matches Admin "Pending Leave Requests")
INSERT INTO leaves (emp_id, from_date, to_date, type, reason) VALUES 
('EMP001', '2026-01-28', '2026-01-29', 'casual', N'Family event'),
('EMP002', '2026-01-27', '2026-01-27', 'sick', N'Fever'),
('EMP001', '2026-02-10', '2026-02-12', 'sick', N'Flu');

-- Attendance sample
INSERT INTO attendance (emp_id, date, status, login_time) VALUES 
('EMP001', '2026-02-02', 'present', '2026-02-02 09:00:00'),
('EMP002', '2026-02-02', 'present', '2026-02-02 09:15:00');


SELECT 'Employees', COUNT(*) FROM employees
UNION ALL SELECT 'Leaves', COUNT(*) FROM leaves;

SELECT emp_id, name, department, FORMAT(doj, 'dd-MMM-yy') as doj, status 
FROM employees ORDER BY emp_id;

-- dashboard queries
-- 1. Admin: Total Active Employees
SELECT COUNT(*) as totalEmployees 
FROM employees WHERE status = 'active';

-- 2. Admin: Pending Leaves (for dashboard cards)
SELECT COUNT(*) as pendingLeaves 
FROM leaves WHERE status = 'pending';

-- 3. Employee: My Total Leaves Applied
SELECT COUNT(*) as myLeaves 
FROM leaves WHERE emp_id = 'EMP001';

-- 4. Employee: My Pending Leaves
SELECT COUNT(*) as myPendingLeaves 
FROM leaves WHERE emp_id = 'EMP001' AND status = 'pending';


-- 5. Complete Employee Directory
SELECT 
    name, 
    emp_id, 
    department, 
    FORMAT(doj, 'dd-MMM-yy') as doj,
    status,
    CASE 
        WHEN status = 'active' THEN 'Active'
        WHEN status = 'on_leave' THEN 'On Leave'
        ELSE 'Inactive'
    END as status_display
FROM employees 
ORDER BY emp_id;

-- leave management queries
-- 6. All Pending Leave Requests (Admin Dashboard)
SELECT 
    e.name, e.emp_id, e.department,
    l.from_date, l.to_date, 
    DATEDIFF(DAY, l.from_date, l.to_date) + 1 as days,
    l.type, l.reason, l.status
FROM leaves l
JOIN employees e ON l.emp_id = e.emp_id
WHERE l.status = 'pending'
ORDER BY l.applied_at DESC;

-- 7. Approve specific leave (use in UPDATE)
UPDATE leaves 
SET status = 'approved' 
WHERE id = 1;

-- 8. My Leave History (Employee)
SELECT from_date, to_date, type, reason, status, applied_at
FROM leaves 
WHERE emp_id = 'EMP001'
ORDER BY applied_at DESC;

-- attendance queries
-- 9. Today's Attendance Summary
SELECT COUNT(*) as todayAttendance
FROM attendance 
WHERE CAST(date AS DATE) = CAST(GETDATE() AS DATE) AND status = 'present';

-- 10. My Attendance This Month
SELECT date, status, login_time, logout_time
FROM attendance 
WHERE emp_id = 'EMP001' 
  AND MONTH(date) = MONTH(GETDATE())
ORDER BY date DESC;

-- 11. Mark Attendance (INSERT)
INSERT INTO attendance (emp_id, date, status, login_time)
VALUES ('EMP001', CAST(GETDATE() AS DATE), 'present', GETDATE());

-- report and analysis
-- 12. Leaves by Department
SELECT 
    e.department,
    COUNT(*) as total_leaves,
    SUM(CASE WHEN l.status = 'pending' THEN 1 ELSE 0 END) as pending
FROM leaves l
JOIN employees e ON l.emp_id = e.emp_id
GROUP BY e.department
ORDER BY total_leaves DESC;

-- 13. Top Leave Takers
SELECT TOP 5
    e.name, e.emp_id,
    COUNT(*) as total_leaves
FROM leaves l
JOIN employees e ON l.emp_id = e.emp_id
GROUP BY e.name, e.emp_id
ORDER BY total_leaves DESC;

-- 14. Monthly Attendance Summary
SELECT 
    MONTH(date) as month,
    COUNT(*) as total_days,
    SUM(CASE WHEN status = 'present' THEN 1 ELSE 0 END) as present_days
FROM attendance
WHERE YEAR(date) = YEAR(GETDATE())
GROUP BY MONTH(date)
ORDER BY month;

-- search and filter
-- 15. Search Employees
SELECT emp_id, name, department, status
FROM employees 
WHERE name LIKE '%John%' 
   OR emp_id LIKE '%EMP%'
   OR department LIKE '%HR%';
