-- auto-generated definition
create table device
(
    id          int auto_increment
        primary key,
    mac_addr    varchar(128)                        null comment 'mac地址',
    memory      text                                null comment '记忆',
    login_time  timestamp                           null comment '登录时间',
    create_time timestamp default CURRENT_TIMESTAMP null comment '创建时间',
    constraint device_pk
        unique (mac_addr)
);

-- 用于存储每个设备每个工具的响应模板
CREATE TABLE `tool_response_templates` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `mac_addr` VARCHAR(128) NOT NULL COMMENT '设备MAC地址',
  `tool_name` VARCHAR(255) NOT NULL COMMENT '工具名称',
  `templates` JSON NOT NULL COMMENT '响应模板，以JSON数组字符串存储',
  `created_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `mac_tool_unique` (`mac_addr`, `tool_name`));



