# note

## database

### models

- User
  - user_id: char
  - twsms_username: char
  - twsms_password: char
- UserSetting
  - fk:user_id
  - pass
- Mobile
  - police_department: char
  - sms_number: char

## funcs

- 使用者設定
  - 不上傳圖片
  - 不輸入車牌
  - 簽名檔
  -

## tomorrow TODO

- msg template
- twsms handling
- peewee
- user settings
- change config.ini to env
