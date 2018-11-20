-- phpMyAdmin SQL Dump
-- version 4.8.3
-- https://www.phpmyadmin.net/
--
-- 主機: localhost
-- 產生時間： 2018 年 11 月 20 日 13:57
-- 伺服器版本: 10.2.18-MariaDB-1:10.2.18+maria~bionic-log
-- PHP 版本： 7.2.10-0ubuntu0.18.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- 資料庫： `floodfire_newsdiff`
--

-- --------------------------------------------------------

--
-- 資料表結構 `page_diff`
--

CREATE TABLE `page_diff` (
  `id` int(11) UNSIGNED NOT NULL,
  `list_id` int(10) UNSIGNED NOT NULL COMMENT '列表編號',
  `url` varchar(1024) NOT NULL COMMENT '新聞網址',
  `url_md5` varchar(32) NOT NULL COMMENT '網址MD5雜湊值',
  `redirected_url` varchar(1024) NOT NULL COMMENT '重新導向後的網址',
  `source_id` tinyint(3) UNSIGNED NOT NULL COMMENT '媒體編號',
  `publish_time` datetime NOT NULL COMMENT '發佈時間',
  `title` text NOT NULL COMMENT '新聞標題',
  `body` text NOT NULL COMMENT '新聞內容',
  `authors` varchar(255) DEFAULT NULL COMMENT '作者（記者）',
  `image` tinyint(1) NOT NULL DEFAULT 0 COMMENT '有無圖片',
  `video` tinyint(1) NOT NULL DEFAULT 0 COMMENT '有無影片',
  `keywords` varchar(255) DEFAULT NULL COMMENT '新聞關鍵字',
  `created_at` datetime DEFAULT NULL COMMENT '建立時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 已匯出資料表的索引
--

--
-- 資料表索引 `page_diff`
--
ALTER TABLE `page_diff`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_source` (`source_id`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `url_md5` (`url_md5`);

--
-- 在匯出的資料表使用 AUTO_INCREMENT
--

--
-- 使用資料表 AUTO_INCREMENT `page_diff`
--
ALTER TABLE `page_diff`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
