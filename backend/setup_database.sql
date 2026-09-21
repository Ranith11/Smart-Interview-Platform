-- SmartInterview — Canonical MySQL Database Setup
-- Run with: mysql -u root -proot < backend/setup_database.sql

CREATE DATABASE IF NOT EXISTS smartinterview
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE smartinterview;

/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answer_evaluations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `answer_id` int NOT NULL,
  `question_id` int NOT NULL,
  `technical_score` int NOT NULL DEFAULT '0',
  `completeness_score` int NOT NULL DEFAULT '0',
  `relevance_score` int NOT NULL DEFAULT '0',
  `semantic_similarity_score` int NOT NULL DEFAULT '0',
  `concept_coverage_score` int NOT NULL DEFAULT '0',
  `overall_score` int NOT NULL DEFAULT '0',
  `feedback` text COLLATE utf8mb4_unicode_ci,
  `strengths` json DEFAULT NULL,
  `weaknesses` json DEFAULT NULL,
  `concepts_expected` json DEFAULT NULL,
  `concepts_found` json DEFAULT NULL,
  `evaluated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `answer_id` (`answer_id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `answer_evaluations_ibfk_1` FOREIGN KEY (`answer_id`) REFERENCES `answers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `answer_evaluations_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `interview_questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=131 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `session_id` int NOT NULL,
  `user_id` int NOT NULL,
  `answer_text` text,
  `submitted_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `question_id` (`question_id`),
  KEY `session_id` (`session_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `answers_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `interview_questions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `answers_ibfk_2` FOREIGN KEY (`session_id`) REFERENCES `interview_sessions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `answers_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=131 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interview_questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `session_id` int NOT NULL,
  `question_number` int NOT NULL,
  `skill` varchar(100) NOT NULL,
  `question_type` varchar(50) NOT NULL,
  `difficulty` enum('easy','medium','hard') NOT NULL,
  `question_text` text NOT NULL,
  `rag_context` json DEFAULT NULL,
  `project_context` json DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `bloom_level` varchar(20) DEFAULT NULL,
  `bloom_level_number` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `session_id` (`session_id`),
  CONSTRAINT `interview_questions_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `interview_sessions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=181 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interview_sessions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `resume_id` int DEFAULT NULL,
  `difficulty` enum('easy','medium','hard') NOT NULL DEFAULT 'medium',
  `question_type` varchar(50) NOT NULL DEFAULT 'mixed',
  `question_count` int NOT NULL DEFAULT '5',
  `selected_skills` json DEFAULT NULL,
  `status` enum('in_progress','completed','abandoned') DEFAULT 'in_progress',
  `started_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  `is_adaptive` tinyint(1) DEFAULT '1',
  `adaptive_state` json DEFAULT NULL,
  `current_bloom_level` varchar(20) DEFAULT NULL,
  `final_recommendations` json DEFAULT NULL,
  `completion_reason` varchar(50) DEFAULT NULL,
  `job_description_id` int DEFAULT NULL,
  `mode` varchar(50) NOT NULL DEFAULT 'normal',
  `syllabus_id` varchar(100) DEFAULT NULL,
  `syllabus_state` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `resume_id` (`resume_id`),
  KEY `fk_interview_sessions_jd` (`job_description_id`),
  CONSTRAINT `fk_interview_sessions_jd` FOREIGN KEY (`job_description_id`) REFERENCES `job_descriptions` (`id`) ON DELETE SET NULL,
  CONSTRAINT `interview_sessions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `interview_sessions_ibfk_2` FOREIGN KEY (`resume_id`) REFERENCES `resumes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job_descriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `filename` varchar(255) NOT NULL,
  `file_path` varchar(500) NOT NULL,
  `skills` json DEFAULT NULL,
  `raw_text` mediumtext,
  `uploaded_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `job_descriptions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resumes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `filename` varchar(255) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `file_path` varchar(500) NOT NULL,
  `skills` json DEFAULT NULL,
  `projects` json DEFAULT NULL,
  `experience` json DEFAULT NULL,
  `education` json DEFAULT NULL,
  `raw_text` mediumtext,
  `page_count` int DEFAULT NULL,
  `uploaded_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `resumes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
