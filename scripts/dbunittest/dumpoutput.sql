PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Person(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
name VARCHAR(255) NOT NULL,
surname VARCHAR(255),
comment VARCHAR(255)
);
INSERT INTO Person VALUES(1,'testname','testnachname','testkommentar');
INSERT INTO Person VALUES(2,'b4Update','lastname','comment');
INSERT INTO Person VALUES(3,'AnotherOne','lastname','comment');
CREATE TABLE Picture(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
personid INTEGER NOT NULL,
data BLOB NOT NULL,
filename VARCHAR(255),
FOREIGN KEY(personid) REFERENCES Person(id)
);
CREATE TABLE Notification(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
address VARCHAR(255) NOT NULL
);
CREATE TABLE PersonNotification(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
personid INTEGER NOT NULL,
notificationid INTEGER NOT NULL,
FOREIGN KEY(personid) REFERENCES Person(id),
FOREIGN KEY(notificationid) REFERENCES Notification(id)
);
CREATE TABLE Command(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
command VARCHAR(255) NOT NULL
);
CREATE TABLE PersonCommand(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
personid INTEGER NOT NULL,
commandid INTEGER NOT NULL,
FOREIGN KEY(personid) REFERENCES Person(id),
FOREIGN KEY(commandid) REFERENCES Command(id)
);
CREATE TABLE Camera(
id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
name VARCHAR(255),
url VARCHAR(255) NOT NULL
);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('Person',39);
INSERT INTO sqlite_sequence VALUES('Picture',37);
COMMIT;
