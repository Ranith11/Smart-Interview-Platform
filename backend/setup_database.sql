-- SmartInterview Week 7 — MySQL Database Setup
-- Run with: mysql -u root -proot < backend/setup_database.sql

CREATE DATABASE IF NOT EXISTS smartinterview
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smartinterview;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    filename        VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    skills          JSON,
    projects        JSON,
    experience      JSON,
    education       JSON,
    raw_text        MEDIUMTEXT,
    page_count      INT,
    uploaded_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Interview sessions table
CREATE TABLE IF NOT EXISTS interview_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NOT NULL,
    resume_id       INT NOT NULL,
    difficulty      ENUM('easy', 'medium', 'hard') NOT NULL DEFAULT 'medium',
    question_type   VARCHAR(50) NOT NULL DEFAULT 'mixed',
    question_count  INT NOT NULL DEFAULT 5,
    selected_skills JSON,
    status          ENUM('in_progress', 'completed', 'abandoned') DEFAULT 'in_progress',
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE
);

-- Interview questions table
CREATE TABLE IF NOT EXISTS interview_questions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    session_id      INT NOT NULL,
    question_number INT NOT NULL,
    skill           VARCHAR(100) NOT NULL,
    question_type   VARCHAR(50) NOT NULL,
    difficulty      ENUM('easy', 'medium', 'hard') NOT NULL,
    question_text   TEXT NOT NULL,
    rag_context     JSON NULL,
    project_context JSON NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE
);

-- Answers table
CREATE TABLE IF NOT EXISTS answers (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    question_id     INT NOT NULL UNIQUE,
    session_id      INT NOT NULL,
    user_id         INT NOT NULL,
    answer_text     TEXT,
    submitted_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES interview_questions(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

SELECT 'SmartInterview database created successfully' AS status;
SHOW TABLES;
