CREATE DATABASE IF NOT EXISTS DEMO;
use Demo;

-- Table structure for table `users`
CREATE TABLE IF NOT EXISTS `CutDateTransform_Record_New` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `driver_id` varchar(10) NOT NULL,
  `CutDay` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `CutDateStartTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `CutDateEndTime` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `drive_time` int(8) NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `idx_driver_id` (`driver_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

-- Table structure for table `posts`
CREATE TABLE IF NOT EXISTS `track_record3_new` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `real_drive` varchar(10) NOT NULL,
  `time_day` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `start_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `drive_time` int(8) NOT NULL,
  `mile` double NOT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `track_record3_new` FOREIGN KEY (`real_drive`) REFERENCES `CutDateTransform_Record`(`driver_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;