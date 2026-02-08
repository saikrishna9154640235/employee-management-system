-- 4. Final Status (NO SUBQUERY)
DECLARE @employeeCount INT;
SELECT @employeeCount = COUNT(*) FROM employees;
PRINT 'EMS Database Setup COMPLETE!';
PRINT 'Total Employees: ' + CAST(@employeeCount AS VARCHAR(10));
GO

-- Test Queries
SELECT 'EMPLOYEES TABLE' AS Table_Name, COUNT(*) AS Record_Count FROM employees
UNION ALL
SELECT 'ATTENDANCE TABLE', COUNT(*) FROM attendance
UNION ALL
SELECT 'LEAVES TABLE', COUNT(*) FROM leaves;
GO

SELECT TOP 5 * FROM employees ORDER BY id DESC;
GO
select * from leaves;
GO

SELECT e.name, e.department, l.* 
FROM employees e 
LEFT JOIN leaves l ON e.emp_id = l.emp_id 
WHERE e.emp_id = 'EMP001';

SELECT e.name, e.department, l.from_date, l.to_date, l.type, l.status
FROM employees e
JOIN leaves l ON e.emp_id = l.emp_id
ORDER BY l.from_date;

-- Check employees (should show 4 records now)
SELECT emp_id, name, department FROM employees ORDER BY emp_id;

-- Check leaves (should show 3 new records)
SELECT emp_id, from_date, to_date, type, status FROM leaves ORDER BY from_date;

-- Full join to see everything together
SELECT e.name, e.department, l.from_date, l.to_date, l.type, l.status
FROM employees e
JOIN leaves l ON e.emp_id = l.emp_id
ORDER BY l.from_date;
