# 簡訊違停報案助手

This is a linebot project that can send illegal parking sms to police department.

## Requirements

- poetry installed
- create a LINE Messaging API
- sign up ngrok

## Development

```sh
poetry install # install dependencies
```

```sh
FLASK_ENV=developement/
FLASK_DEBUG=TRUE /
poetry run flask run # run flask app
```

```sh
ngrok http 8000 # put localhost on the internet
```

Set your linebot webhook address(remember to append '/callback' at end) to ngrok address and have fun!

## Authors

- [@FOBshippingpoint](https://github.com/FOBshippingpoint)

## License

[MIT](https://choosealicense.com/licenses/mit/)
