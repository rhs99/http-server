import gzip
import socket
import argparse
import threading


status_dict = {
    "200": "OK",
    "201": "Created",
    "404": "Not Found",
}


class RequestHandler:
    def __init__(self, conn: socket.socket, args):
        data = conn.recv(1024).decode()
        data_segments = data.split("\r\n")

        self.method = data_segments[0].split(" ")[0]
        self.path = data_segments[0].split(" ")[1]
        self.req_data = data_segments[-1]
        self.headers = data_segments[1:-1]

        self.args = args
        self.conn = conn

    def get_header(self, key):
        for header in self.headers:
            if header.startswith(key):
                return header.split(": ")[1]

    def should_encode(self):
        encoding = self.get_header("Accept-Encoding")
        if encoding is not None and "gzip" in encoding:
            return True
        return False

    def send_renponse(self, status_code, headers=[], data="", compressed_data=None):
        response = f"HTTP/1.1 {status_code} {status_dict[status_code]}\r\n"

        if self.should_encode():
            headers.append("Content-Encoding: gzip")

        if len(headers) == 0:
            response = f"{response}\r\n"
        else:
            for header in headers:
                key, value = header.split(": ")
                response = f"{response}{key}: {value}\r\n"

        response = f"{response}\r\n{data}"

        self.conn.send(
            response.encode() + compressed_data
            if compressed_data
            else response.encode()
        )
        self.conn.close()

    def handle_request(self):
        if self.path == "/":
            return self.send_renponse(status_code="200")
        elif self.path.startswith("/echo"):
            remaining_path = self.path[6:]

            encode = self.should_encode()
            if encode:
                remaining_path = gzip.compress(remaining_path.encode())

            return self.send_renponse(
                status_code="200",
                headers=[
                    "Content-Type: text/plain",
                    f"Content-Length: {len(remaining_path)}",
                ],
                data="" if encode else remaining_path,
                compressed_data=remaining_path if encode else None,
            )
        elif self.path == "/user-agent":
            user_agent = self.get_header("User-Agent")
            return self.send_renponse(
                status_code="200",
                headers=[
                    "Content-Type: text/plain",
                    f"Content-Length: {len(user_agent)}",
                ],
                data=user_agent,
            )
        elif self.path.startswith("/files"):
            dir = args.directory
            file_name = self.path[7:]

            if self.method == "POST":
                try:
                    with open(
                        f"/{dir}/{file_name}",
                        "w",
                    ) as f:
                        f.write(self.req_data)
                    return self.send_renponse(
                        status_code="201",
                        headers=[
                            "Content-Type: application/octet-stream",
                            f"Content-Length: {len(self.req_data)}",
                        ],
                        data=self.req_data,
                    )
                except Exception as e:
                    return self.send_renponse(status_code="404")
            elif self.method == "GET":
                try:
                    with open(
                        f"/{dir}/{file_name}",
                        "r",
                    ) as f:
                        content = f.read()
                    return self.send_renponse(
                        status_code="200",
                        headers=[
                            "Content-Type: application/octet-stream",
                            f"Content-Length: {len(content)}",
                        ],
                        data=content,
                    )
                except Exception as e:
                    return self.send_renponse(status_code="404")
        else:
            return self.send_renponse(status_code="404")


def conn_handler(conn: socket.socket, args):
    requesr_handler = RequestHandler(conn, args)
    requesr_handler.handle_request()


def main(args):
    server_socket = socket.create_server(
        (
            "localhost",
            4221,
        ),
        reuse_port=True,
    )
    while True:
        conn, _ = server_socket.accept()
        threading.Thread(
            target=conn_handler,
            args=(conn, args),
        ).start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", default=".")
    args = parser.parse_args()

    main(args)
