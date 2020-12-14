import socket
import sounddevice as sd
import pickle
import threading
import queue
import sys

localCredentials = {
    'IP': '',
    'PORT': 9000
}
remoteCredentials = {
    'IP': sys.argv[1],
    'PORT': int(sys.argv[2])
}
q_in = queue.Queue()
q_out = queue.Queue()

peer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
peer.bind((localCredentials['IP'], localCredentials['PORT']))


def reliable_recv(sock):
    message = b''
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            message += data
            return pickle.loads(message), addr
        except ValueError:
            continue


def send_media(sock):
    while True:
        try:
            data = q_in.get(timeout=1)
            data = pickle.dumps(data)
        except queue.Empty:
            sys.exit()
        sock.sendto(data, (remoteCredentials['IP'], remoteCredentials['PORT']))


def recv_media(sock):
    while True:
        data, addr = reliable_recv(sock)
        q_out.put(data)


def input_callback(indata, frame, time, status):
    if status:
        print(status)
    q_in.put(indata.copy())


def audio_call_input():
    with sd.InputStream(blocksize=200, channels=2, dtype='float32', callback=input_callback):
        while True:
            sd.sleep(1)  # unlimited time call


def output_callback(outdata, frame, time, status):
    if status:
        print(status)
    try:
        outdata[:] = q_out.get_nowait()
    except queue.Empty:
        raise sd.CallbackAbort


def audio_call_output():
    with sd.OutputStream(blocksize=200, channels=2, dtype='float32', callback=output_callback):
        while True:
            sd.sleep(1)  # unlimited call


def main():
    thread1 = threading.Thread(target=send_media, args=(peer,))
    thread2 = threading.Thread(target=audio_call_input)
    thread3 = threading.Thread(target=recv_media, args=(peer,))
    thread4 = threading.Thread(target=audio_call_output)
    thread2.start()
    thread1.start()
    thread3.start()
    while not (q_out.qsize() > 100):
        print(q_out.qsize())
    thread4.start()


if __name__ == "__main__":
    main()
