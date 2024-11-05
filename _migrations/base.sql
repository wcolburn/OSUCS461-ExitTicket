
CREATE TABLE `user` (
  `uuid` varchar(56) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `time_created` int(11) DEFAULT NULL,
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `user_post` (
  `uuid` varchar(65) NOT NULL,
  `user_uuid` varchar(56) DEFAULT NULL,
  `post_9char` varchar(9) DEFAULT NULL,
  `text` longtext DEFAULT NULL,
  `time_created` int(11) DEFAULT NULL,
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
