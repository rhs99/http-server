# Python HTTP Server

## Features

- Supports concurrent request handling using multi-threading
- Supprots data compression (`gzip`)
- Supports sending file data as response

### Usage
To run the server use
`python app/main.py --directory /tmp`

Send request to the server:
`curl -v localhost:4221`