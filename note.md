# note

## 給明天的我

- 正在 refactor
- 看 doc tutorial
- "How to generate good secret keys"
- <https://flask.palletsprojects.com/en/2.1.x/tutorial/install/>

## TODO

- instructions
  - i will write wiki for that.
- bugs report
- store address, image links for further use.
- legal
  - privacy policy
  - terms of use
- ?
  - UserSession.username & UserSession.password may not need.

```python
# legacy
# used in liff framework
@app.route("/liff/set-twsms-account", methods=["POST"])
def set_twsms_account():
    print("hello")
    token_type, access_token = request.headers.get("Authorization").split(" ")
    print(token_type, access_token)
    print(request.get_json())
    if token_type != "Bearer" or token_type is None:
        return
    r = requests.get(
        "https://api.line.me/oauth2/v2.1/verify",
        params={"access_token": access_token},
    )
    if r.status_code != 200:
        return abort(400)
    # save to username, password to database
    data = request.get_json()
    user, created = User.get_or_create(
        user_id=data["user_id"],
        twsms_username=data["username"],
        twsms_password=data["password"],
    )
    if user:
        # if exist, update
        user.twsms_username = data["username"]
        user.twsms_password = data["password"]
```
