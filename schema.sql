CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    purok VARCHAR(100) DEFAULT '',
    contact VARCHAR(20) DEFAULT '',
    role VARCHAR(20) NOT NULL DEFAULT 'resident'
);

CREATE TABLE IF NOT EXISTS concerns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) DEFAULT 'General',
    status VARCHAR(30) DEFAULT 'Pending',
    resident_id INT NULL,
    assigned_staff_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_concerns_resident (resident_id),
    INDEX idx_concerns_staff (assigned_staff_id)
);

