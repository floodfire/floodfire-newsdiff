-- phpMyAdmin SQL Dump
-- version 4.8.3
-- https://www.phpmyadmin.net/
--
-- 主機: localhost
-- 產生時間： 2018 年 10 月 21 日 20:30
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
-- 資料表結構 `list`
--

CREATE TABLE `list` (
  `id` int(11) NOT NULL,
  `url` varchar(1024) NOT NULL COMMENT '新聞網址',
  `url_md5` varchar(32) NOT NULL COMMENT '網址MD5雜湊值',
  `source_id` tinyint(3) UNSIGNED NOT NULL COMMENT '媒體編號',
  `category` varchar(50) NOT NULL COMMENT '新聞類別',
  `title` text NOT NULL COMMENT '新聞標題',
  `created_at` datetime NOT NULL COMMENT '連結建立時間',
  `crawler_count` tinyint(3) UNSIGNED NOT NULL DEFAULT 0 COMMENT '爬抓次數',
  `error_count` tinyint(4) NOT NULL DEFAULT 0 COMMENT '發生錯誤次數'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 資料表結構 `page`
--

CREATE TABLE `page` (
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

-- --------------------------------------------------------

--
-- 資料表結構 `page_raw`
--

CREATE TABLE `page_raw` (
  `id` int(10) UNSIGNED NOT NULL,
  `link_id` int(10) UNSIGNED NOT NULL COMMENT '列表編號',
  `url` varchar(1024) NOT NULL COMMENT '新聞網址',
  `url_md5` varchar(32) NOT NULL COMMENT '網址MD5雜湊值',
  `page_content` mediumtext NOT NULL COMMENT '原始內容',
  `created_at` datetime NOT NULL COMMENT '建立時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- --------------------------------------------------------

--
-- 資料表結構 `source`
--

CREATE TABLE `source` (
  `id` tinyint(3) UNSIGNED NOT NULL COMMENT '編號',
  `code_name` varchar(20) NOT NULL COMMENT '英文代稱',
  `media_name` varchar(50) NOT NULL COMMENT '媒體名稱',
  `note` text NOT NULL COMMENT '備註'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- 資料表的匯出資料 `source`
--

INSERT INTO `source` (`id`, `code_name`, `media_name`, `note`) VALUES
(1, 'apd', '蘋果日報', ''),
(2, 'cnt', '中時電子報', ''),
(3, 'cna', '中央社', ''),
(4, 'ett', '東森新聞', ''),
(5, 'ltn', '自由時報', ''),
(6, '', '新頭穀', ''),
(7, '', 'nownews', ''),
(8, 'udn', '聯合新聞網', ''),
(9, '', 'TVBS', ''),
(10, '', '中廣新聞網', ''),
(11, '', '公視新聞網', ''),
(12, '', '台視新聞', ''),
(13, '', '華視新聞', ''),
(14, '', '民視新聞', ''),
(15, '', '三立新聞', ''),
(16, '', '風傳媒', ''),
(17, '', '關鍵評論網', '');

-- --------------------------------------------------------

--
-- 資料表結構 `visual_link`
--

CREATE TABLE `visual_link` (
  `id` int(10) UNSIGNED NOT NULL COMMENT '編號',
  `type` tinyint(3) UNSIGNED NOT NULL COMMENT '列表編號（1: pic, 2: video）',
  `list_id` int(10) UNSIGNED NOT NULL COMMENT '頁面編號',
  `url_md5` varchar(32) NOT NULL COMMENT '網址MD5雜湊值',
  `visual_src` varchar(1024) NOT NULL COMMENT '圖像連結位址',
  `caption` varchar(255) DEFAULT NULL COMMENT '圖像標題內容',
  `created_at` datetime NOT NULL COMMENT '建立時間'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='抽取圖片或是影片網址';

--
-- 已匯出資料表的索引
--

--
-- 資料表索引 `list`
--
ALTER TABLE `list`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_source` (`source_id`),
  ADD KEY `url_md5` (`url_md5`),
  ADD KEY `crawler_count` (`crawler_count`),
  ADD KEY `error_count` (`error_count`);

--
-- 資料表索引 `page`
--
ALTER TABLE `page`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_source` (`source_id`),
  ADD KEY `idx_created_at` (`created_at`),
  ADD KEY `url_md5` (`url_md5`);

--
-- 資料表索引 `page_raw`
--
ALTER TABLE `page_raw`
  ADD PRIMARY KEY (`id`);

--
-- 資料表索引 `source`
--
ALTER TABLE `source`
  ADD PRIMARY KEY (`id`);

--
-- 資料表索引 `visual_link`
--
ALTER TABLE `visual_link`
  ADD PRIMARY KEY (`id`),
  ADD KEY `url_md5` (`url_md5`);

--
-- 在匯出的資料表使用 AUTO_INCREMENT
--

--
-- 使用資料表 AUTO_INCREMENT `list`
--
ALTER TABLE `list`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- 使用資料表 AUTO_INCREMENT `page`
--
ALTER TABLE `page`
  MODIFY `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- 使用資料表 AUTO_INCREMENT `page_raw`
--
ALTER TABLE `page_raw`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- 使用資料表 AUTO_INCREMENT `visual_link`
--
ALTER TABLE `visual_link`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '編號';
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
