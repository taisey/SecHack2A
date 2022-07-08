 -- ユーザ管理テーブル
 CREATE TABLE IF NOT EXISTS `DB`.`Users`(
     `user_id` CHAR(48) NOT NULL,
     `happy` FLOAT NOT NULL,
     `angry` FLOAT NOT NULL,
     `disgusted` FLOAT NOT NULL,
     `sad` FLOAT NOT NULL ,
     `fearful` FLOAT NOT NULL ,
     `neutral` FLOAT NOT NULL ,
     `surprised` FLOAT NOT NULL ,
     `createdBy` DATETIME,         
     PRIMARY KEY (`user_id`));

