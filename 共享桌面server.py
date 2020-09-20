import sys
import threading
import numpy
import socket
from PIL import ImageGrab
from PIL import Image
from io import BytesIO


class WebServer(object):
    def __init__(self, port):
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # UDP协议
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        self.server_socket.bind(('', self.port))
        self.server_socket.listen(128)  # UDP方式会引发，OSError: [WinError 10045] 参考的对象类型不支持尝试的操作。

    @staticmethod
    def handle_request(client_socket, ip_port):
        recv_data = client_socket.recv(1024)
        if len(recv_data) == 0:
            # print(ip_port, '：客户端已经下线')
            client_socket.close()
            return

        request_path = recv_data.decode('utf-8').split(' ', maxsplit=2)[1]
        request_path = request_path.split('?')[0]
        # print('request_path:', request_path)
        if request_path == "/getdesktop/":
            data = ('HTTP/1.1 200 OK\r\n' + 'Server:NB1.0\r\ncontent-type: image/jpeg\r\n' + '\r\n').encode('utf-8')
            desk_img = ImageGrab.grab()
            re_desk_img = desk_img.resize((1280, 720), Image.ANTIALIAS)
            bio = BytesIO()
            re_desk_img.save(bio, format='JPEG')
            jpeg_array = numpy.array(Image.open(bio))
            bio.close()
            bio = BytesIO()
            pic = Image.fromarray(jpeg_array)
            pic.save(bio, format='JPEG')
            jpeg = bio.getvalue()
            bio.close()
            client_socket.send(data + jpeg)
            client_socket.close()
        elif request_path == "/":
            with open('static/index.html', 'rb') as f:
                body = f.read()
            data = ('HTTP/1.1 200 OK\r\n' + 'Server:NB1.0\r\n' + '\r\n').encode('utf-8')
            client_socket.send(data + body)
            client_socket.close()
        else:
            try:
                with open('static' + request_path, 'rb') as f:
                    body = f.read()
                data = ('HTTP/1.1 200 OK\r\n' + 'Server:NB1.0\r\n' + '\r\n').encode('utf-8') + body
                client_socket.send(data)
            except Exception as e:
                data = ('HTTP/1.1 404 Not Found\r\n' + 'Server:NB1.0\r\n' + '\r\n' + '资源不存在').encode('utf-8')
                client_socket.send(data)
            finally:
                client_socket.close()

    @staticmethod
    def get_host_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
        except Exception as e:
            print(e)
            ip = "0.0.0.0"
        return ip

    def run(self):
        # print('启动成功：', socket.gethostbyname(socket.gethostname()), self.port)
        print('启动成功：', self.get_host_ip()+':'+str(self.port))
        while True:
            client_socket, ip_port = self.server_socket.accept()
            # print('客户端连接：', ip_port)
            sub_threading = threading.Thread(target=self.handle_request, args=(client_socket, ip_port))
            sub_threading.setDaemon(True)
            sub_threading.start()


if __name__ == '__main__':
    port = 8000
    if len(sys.argv) == 2:
        if sys.argv[1].isdigit():
            port = int(sys.argv[1])
    server = WebServer(port)
    server.run()
