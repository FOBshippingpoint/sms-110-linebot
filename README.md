# 簡訊違停報案助手

## Requirements

- poetry installed
- sign up a line developer username
- set your own CHANNEL*ACCESS_TOKEN and CHANNEL_SECRET in \_config.ini*
- sign up ngrok

## Development

```sh
poetry install # install dependencies
```

```sh
poetry run python sms_110_linebot/app.py
```

```sh
ngrok http 8000 # put localhost on the internet, you can change port number in app.py
```

Set your linebot webhook address to ngrok address and have fun!

## Todo

- delete expired users
- edit message
- create message template
- ...

## Authors

- [@FOBshippingpoint](https://github.com/FOBshippingpoint)

## License

[MIT](https://choosealicense.com/licenses/mit/)
