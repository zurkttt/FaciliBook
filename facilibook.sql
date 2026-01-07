-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 07, 2026 at 03:57 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `facilibook`
--

-- --------------------------------------------------------

--
-- Table structure for table `bookings`
--

CREATE TABLE `bookings` (
  `id` int(11) NOT NULL,
  `facility_id` int(11) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `purpose` varchar(255) DEFAULT NULL,
  `status` enum('pending','approved','rejected') DEFAULT 'pending',
  `approved_by` int(11) DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `bookings`
--

INSERT INTO `bookings` (`id`, `facility_id`, `user_id`, `start_time`, `end_time`, `purpose`, `status`, `approved_by`, `rejection_reason`) VALUES
(1, 1, 2, '2026-01-05 07:20:00', '2026-01-05 10:20:00', 'Test1', 'approved', NULL, NULL),
(2, 2, 2, '2026-01-06 07:20:00', '2026-01-06 12:00:00', 'Test2', 'rejected', NULL, NULL),
(4, 2, 3, '2026-01-07 08:40:00', '2026-01-07 12:00:00', 'Test4', 'approved', 1, NULL),
(5, 1, 3, '2025-12-30 08:00:00', '2025-12-30 10:00:00', 'testtt', 'rejected', NULL, NULL),
(8, 1, 3, '2026-01-08 08:00:00', '2026-01-08 10:00:00', 'Role Play', 'approved', 1, NULL),
(9, 2, 4, '2026-01-08 08:00:00', '2026-01-08 09:00:00', 'Competition', 'approved', 1, NULL),
(10, 3, 4, '2026-01-09 08:00:00', '2026-01-09 17:00:00', 'Basketball Tourna', 'approved', 1, NULL),
(11, 1, 4, '2026-01-12 08:00:00', '2026-01-12 10:00:00', 'Final Exam', 'rejected', NULL, 'University Event'),
(12, 2, 4, '2026-01-12 08:00:00', '2026-01-12 10:00:00', 'Cinema', 'rejected', NULL, 'Trip ko lang'),
(13, 1, 5, '2026-01-13 08:00:00', '2026-01-13 12:00:00', 'Role Play Competion', 'approved', 1, NULL),
(14, 3, 2, '2026-01-12 08:00:00', '2026-01-12 10:00:00', 'PE Activity', 'pending', NULL, NULL),
(15, 2, 2, '2026-01-14 08:00:00', '2026-01-14 10:00:00', 'Role Play ', 'pending', NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `facilities`
--

CREATE TABLE `facilities` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `capacity` int(11) DEFAULT NULL,
  `status` enum('active','maintenance') DEFAULT 'active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `facilities`
--

INSERT INTO `facilities` (`id`, `name`, `description`, `capacity`, `status`) VALUES
(1, 'Amphitheater', 'For big events', 450, 'active'),
(2, 'SAC', 'For Performance Task', 120, 'active'),
(3, 'Covered Court', 'Physical Activities', 80, 'active'),
(4, 'Computer Lab', 'Best Specs Computer', 40, 'active');

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `id` int(11) NOT NULL,
  `booking_id` int(11) NOT NULL,
  `rating` int(11) DEFAULT NULL CHECK (`rating` between 1 and 5),
  `remarks` text DEFAULT NULL,
  `date_submitted` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `feedback`
--

INSERT INTO `feedback` (`id`, `booking_id`, `rating`, `remarks`, `date_submitted`) VALUES
(1, 1, 4, 'Test', '2026-01-07 19:30:02'),
(2, 4, 5, 'Nothing', '2026-01-07 22:01:13');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','faculty') NOT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `username`, `password`, `role`, `is_active`) VALUES
(1, 'System Admin', 'admin', 'admin', 'admin', 1),
(2, 'Dill Doe', 'test', 'test', 'faculty', 1),
(3, 'Test2', 'Test2', 'test2', 'faculty', 1),
(4, 'Test Test', 'test3', 'test3', 'faculty', 1),
(5, 'Johny Bravo', 'Johnjohn', 'johnjohn', 'faculty', 1),
(6, 'Shibal Jinja', 'shibal', 'shibal', 'faculty', 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `bookings`
--
ALTER TABLE `bookings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `facility_id` (`facility_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `fk_approver` (`approved_by`);

--
-- Indexes for table `facilities`
--
ALTER TABLE `facilities`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`id`),
  ADD KEY `booking_id` (`booking_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `bookings`
--
ALTER TABLE `bookings`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT for table `facilities`
--
ALTER TABLE `facilities`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `bookings`
--
ALTER TABLE `bookings`
  ADD CONSTRAINT `bookings_ibfk_1` FOREIGN KEY (`facility_id`) REFERENCES `facilities` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `bookings_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_approver` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`);

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
