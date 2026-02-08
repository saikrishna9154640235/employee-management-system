
USE project;
GO

-- 1. Create Database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ems_db')
BEGIN
    CREATE DATABASE ems_db;
    PRINT '✅ Database ems_db created';
END
GO

USE ems_db;
GO



-- Drop in correct order (children first due to FKs)
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS leaves;
DROP TABLE IF EXISTS employees;
PRINT 'All tables dropped successfully';







