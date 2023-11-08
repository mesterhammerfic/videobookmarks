INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO tag_list (user_id, name, description, created)
VALUES
  (1, 'test_1', "test_description", '2018-01-01 00:00:00'),
  (2, 'test_2', "", '2018-01-01 00:00:00');

INSERT INTO video (link)
VALUES
  ('test_link'),
  ('another_link');

INSERT INTO tag (user_id, tag_list_id, video_id, youtube_timestamp, tag, created)
VALUES
  --this is the main tag that the rest of the descriptions are comparing to
  (1, 1, 1, 1.0, 'tag_1', '2018-01-01 00:00:00'),
  --this tag is on the same video and the same tag_list but from a dif user
  (2, 1, 1, 2.0, 'tag_2', '2018-01-01 00:00:00'),
  --this tag is on the same user and the same video but from a dif tag_list
  (1, 2, 1, 3.0, 'tag_3', '2018-01-01 00:00:00'),
  --this tag is on the same user and the same tag_list but from a dif video
  (1, 1, 2, 4.0, 'tag_4', '2018-01-01 00:00:00'),
  --this is the same user, video, tag_list and on the same timestamp, but a different tag
  (1, 1, 1, 1.0, 'tag_5', '2018-01-01 00:00:00'),
  --this is the same user, video, tag_list, and tag but at a different time
  (1, 1, 1, 5.0, 'tag_5', '2018-01-01 00:00:00');