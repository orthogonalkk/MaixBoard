import threading
import time
import os
import socket
import select
import cv2

# import queue

################################################################
# global

g_wifi_name = "Navigation"
g_wifi_password = "00000000"

g_cond_connected = threading.Condition()
g_is_connected = False
g_client_address = None
g_resource_rc = 0

# g_tcp_send_queue = queue.Queue()


# Suppress print.
# def print(*args, **kwargs):
#     pass

def run_connect_wifi_command():
    os.system(f"wifi_connect_ap_test {g_wifi_name} {g_wifi_password}")


################################################################
# utils


def try_wait_for_connected(timeout):
    with g_cond_connected:
        return g_cond_connected.wait_for(lambda: g_is_connected, timeout)


def wait_for_connected():
    with g_cond_connected:
        g_cond_connected.wait_for(lambda: g_is_connected)


def try_wait_for_disconnected(timeout):
    with g_cond_connected:
        return g_cond_connected.wait_for(lambda: not g_is_connected, timeout)


def wait_for_disconnected():
    with g_cond_connected:
        g_cond_connected.wait_for(lambda: not g_is_connected)


def wait_for_resource_released():
    with g_cond_connected:
        g_cond_connected.wait_for(lambda: g_resource_rc == 0)


################################################################
# broadcast_thread_routine

UDP_PORT = 11451


def get_host_ip():
    """
    如果没有网络，则会抛出异常。可以用来判断是否已连接网络。
    """
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.connect(("10.255.255.255", 1))
    return str(so.getsockname()[0])


def make_broadcast_ip(ip):
    ip = ip.split(".")
    ip[-1] = "255"
    return ".".join(ip)


def make_identity():
    return b"V831"


def broadcast_identity():
    print("broadcast identity")
    ip = make_broadcast_ip(get_host_ip())
    address = (ip, UDP_PORT)
    so = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    so.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    so.sendto(make_identity(), address)
    so.close()


def broadcast_thread_routine():
    while True:
        while not g_is_connected:
            try:
                broadcast_identity()
            except Exception:  # TODO: broadcast_identity 可能会抛出异常。
                pass
            if try_wait_for_connected(1):
                break
        wait_for_disconnected()
        wait_for_resource_released()


################################################################
# camera_thread_routine

JPEG_PORT = 38892
CAMERA_ID = 2


class OpenCVCamera:
    def __init__(self, device=0):
        self.cap = cv2.VideoCapture(device)

    def close(self):
        self.cap.release()

    def capture(self):
        result, frame = self.cap.read()
        return frame if result else None


g_opencv_camera = None


def sample_as_jpeg() -> bytes:
    img = g_opencv_camera.capture()
    if img is None:
        return None
    params = [cv2.IMWRITE_JPEG_QUALITY, 80]
    result, jpg_img = cv2.imencode(".jpg", img, params)
    if not result:
        return None
    img_bytes = jpg_img.tobytes()
    return img_bytes


def make_full_packet(jpeg_data) -> bytes:
    return jpeg_data


def camera_thread_routine():
    global g_resource_rc

    global g_opencv_camera

    while True:
        wait_for_connected()

        g_opencv_camera = OpenCVCamera(CAMERA_ID)
        with g_cond_connected:
            g_resource_rc += 1
            g_cond_connected.notify_all()

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (g_client_address, JPEG_PORT)
        while g_is_connected:
            jpeg_data = sample_as_jpeg()
            # 如果采样失败，就认为 USB 摄像头断开连接。
            # 重新创建摄像头对象。
            if not jpeg_data:
                g_opencv_camera.close()
                g_opencv_camera = OpenCVCamera(CAMERA_ID)
                continue
            full_packet = make_full_packet(jpeg_data)
            print("jpeg size:", len(full_packet))

            SIZE = 65507
            for sub_packet in (
                full_packet[i : i + SIZE] for i in range(0, len(full_packet), SIZE)
            ):
                try:
                    client_socket.sendto(sub_packet, address)
                except Exception:
                    break  # TODO: 细化异常处理。
            try:
                client_socket.sendto(b"end", address)
            except Exception:
                continue  # TODO: 细化异常处理。

        wait_for_disconnected()

        g_opencv_camera.close()
        g_opencv_camera = None
        with g_cond_connected:
            g_resource_rc -= 1
            g_cond_connected.notify_all()


################################################################
# motor_thread_routine


def motor_thread_routine():
    global g_resource_rc

    while True:
        wait_for_connected()
        with g_cond_connected:
            g_resource_rc += 1
            g_cond_connected.notify_all()

        wait_for_disconnected()
        with g_cond_connected:
            g_resource_rc -= 1
            g_cond_connected.notify_all()


################################################################
# tcp_thread_routine

TCP_PORT = 6666


def tcp_thread_routine():
    global g_is_connected
    global g_client_address

    # global g_tcp_send_queue

    while True:
        retry_count = 0
        run_connect_wifi_command()
        while retry_count <= 3:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # https://blog.csdn.net/u012206617/article/details/105851649
            # 当有一个有相同本地地址和端口的 socket1 处于 TIME_WAIT 状态时，
            # 而你启动的程序的 socket2 要占用该地址和端口，
            # 你的程序就要用到 SO_REUSEADDR。
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server_socket.bind(("", TCP_PORT))
                server_socket.listen(1)
                try:
                    server_socket.settimeout(5)
                    conn, client_address = server_socket.accept()
                except Exception:
                    # TODO: 检查是不是表示没联网。
                    time.sleep(1)
                    break
                # 客户端已经通过 connect 使得连接建立。
                print("socket connected")
                with g_cond_connected:
                    g_is_connected = True
                    g_client_address = client_address[0]
                    g_cond_connected.notify_all()

                # 不断收发数据，直到客户端断开连接。
                server_socket.settimeout(2)
                conn.setblocking(0)
                while True:
                    # 收数据。
                    try:
                        # 假设 recv 总是能有效地在连接断开时自动返回或抛出异常。
                        ready = select.select([conn], [], [], 2)
                        received_data = conn.recv(2048) if ready[0] else None
                        # When the remote end is closed and all data is read,
                        # return the empty string.
                        # 注意：收到空必须重新创建 socket，但不一定代表完全断开了。
                        if not received_data:
                            break
                    except Exception as e:
                        print(e)
                        # TODO: 细化 recv 的异常处理。
                        break

                    # TODO: 处理收到的数据。
                    retry_count = 0
                    print(len(received_data))

                    # 发数据。发数据是不重要的，所以不用考虑并发收发。
                    # while not g_tcp_send_queue.empty():
                    #     send_data = g_tcp_send_queue.get_nowait()
                    #     conn.sendall(send_data)

            finally:
                server_socket.close()
                print("socket closed")
                retry_count += 1
        with g_cond_connected:
            g_is_connected = False
            g_client_address = None
            g_cond_connected.notify_all()
        wait_for_resource_released()
        print("wait for resource released successfully")


################################################################


def run_system_command(safe_delay=3, post_delay=0):
    time.sleep(safe_delay)
    os.system('echo "usb_host" > /sys/devices/platform/soc/usbc0/otg_role')
    time.sleep(post_delay)


if __name__ == "__main__":
    run_system_command()
    # 等待网络连接。
    while True:
        try:
            get_host_ip()
            break
        except Exception:
            time.sleep(1)

    threading.Thread(target=broadcast_thread_routine).start()
    threading.Thread(target=camera_thread_routine).start()
    threading.Thread(target=motor_thread_routine).start()
    tcp_thread_routine()
