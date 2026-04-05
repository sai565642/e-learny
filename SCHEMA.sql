-- e-Learny Platform | Database Schema Dump
-- Created by SAI Coder

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for auth_user
-- ----------------------------
CREATE TABLE IF NOT EXISTS `auth_user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL DEFAULT 0,
  `username` varchar(150) NOT NULL UNIQUE,
  `first_name` varchar(150) DEFAULT NULL,
  `last_name` varchar(150) DEFAULT NULL,
  `email` varchar(254) NOT NULL UNIQUE,
  `is_staff` tinyint(1) NOT NULL DEFAULT 0,
  `is_active` tinyint(1) NOT NULL DEFAULT 1,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for user_management_app_profile
-- ----------------------------
CREATE TABLE IF NOT EXISTS `user_management_app_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL UNIQUE,
  `mobile` varchar(15) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `dob` date DEFAULT NULL,
  `gender` varchar(20) DEFAULT NULL,
  `occupational_status` varchar(20) DEFAULT 'Student',
  `is_approved` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_profile_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_course_category
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_course_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_language
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_language` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `slug` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_course
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_course` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `title` varchar(250) NOT NULL,
  `slug` varchar(255) NOT NULL UNIQUE,
  `description` text,
  `thumbnail` varchar(200) DEFAULT NULL,
  `level` varchar(20) DEFAULT 'Beginner',
  `category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `original_price` decimal(10,2) DEFAULT '0.00',
  `discount_price` decimal(10,2) DEFAULT '0.00',
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  `course_active` tinyint(1) DEFAULT 1,
  `trending` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_course_cat` FOREIGN KEY (`category_id`) REFERENCES `courses_app_course_category` (`id`),
  CONSTRAINT `fk_course_lang` FOREIGN KEY (`language_id`) REFERENCES `courses_app_language` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_course_instructors
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_course_instructors` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `course_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_inst_course` FOREIGN KEY (`course_id`) REFERENCES `courses_app_course` (`id`),
  CONSTRAINT `fk_inst_user` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_section
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_section` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `course_id` bigint NOT NULL,
  `title` varchar(255) NOT NULL,
  `order` int NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `slug` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_sub_section
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_sub_section` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `section_id` bigint NOT NULL,
  `title` varchar(255) NOT NULL,
  `order` int NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `slug` varchar(255) NOT NULL,
  `course_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_video
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_video` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sub_section_id` bigint NOT NULL,
  `title` varchar(255) NOT NULL,
  `video_file` varchar(255) NOT NULL,
  `order` int NOT NULL,
  `course_id` bigint NOT NULL,
  `section_id` bigint NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `slug` varchar(255) NOT NULL,
  `thumbnail` varchar(255) DEFAULT NULL,
  `demo` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for courses_app_document
-- ----------------------------
CREATE TABLE IF NOT EXISTS `courses_app_document` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sub_section_id` bigint NOT NULL,
  `title` varchar(255) NOT NULL,
  `document` varchar(255) NOT NULL,
  `order` int NOT NULL,
  `course_id` bigint NOT NULL,
  `category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `slug` varchar(255) NOT NULL,
  `section_id` bigint NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for purchases_app_coursespurchased
-- ----------------------------
CREATE TABLE IF NOT EXISTS `purchases_app_coursespurchased` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `course_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `course_category_id` bigint DEFAULT NULL,
  `language_id` bigint DEFAULT NULL,
  `date` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for student_video_progress
-- ----------------------------
CREATE TABLE IF NOT EXISTS `student_video_progress` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `video_id` bigint NOT NULL,
  `is_completed` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Table structure for contact_messages
-- ----------------------------
CREATE TABLE IF NOT EXISTS `contact_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `message` text NOT NULL,
  `created_at` datetime(6) DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Final initialization for Admin (Manual step required)
-- ----------------------------
-- Manual insert of categories:
-- INSERT INTO courses_app_course_category (id, name) VALUES (10, 'Development'), (11, 'Backend'), (12, 'Mobile');

SET FOREIGN_KEY_CHECKS = 1;
