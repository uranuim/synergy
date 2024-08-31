import socket
import cv2
import numpy as np
import pyaudio
import threading

# Set up the video client socket
video_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_client_socket.connect(('192.168.223.156', 9000))

# Set up the audio client socket
audio_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_client_socket.connect(('192.168.223.156', 11000))

# Initialize audio playback
p = pyaudio.PyAudio()
audio_stream = p.open(format=pyaudio.paInt16,
                      channels=1,
                      rate=44100,
                      output=True,
                      frames_per_buffer=1024)

def receive_audio():
    while True:
        audio_data = audio_client_socket.recv(1024)
        if not audio_data:
            break
        audio_stream.write(audio_data)

# Start audio receiving thread
audio_thread = threading.Thread(target=receive_audio)
audio_thread.start()

while True:
    # Read the length of the frame first
    length = int.from_bytes(video_client_socket.recv(4), byteorder='big')
    
    # Read the frame itself
    frame_data = b""
    while len(frame_data) < length:
        packet = video_client_socket.recv(length - len(frame_data))
        if not packet:
            break
        frame_data += packet
    
    # Decode and display the frame
    frame = np.frombuffer(frame_data, dtype=np.uint8)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    
    if frame is not None:
        cv2.imshow('Client - Receiving Video', frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cv2.destroyAllWindows()
video_client_socket.close()
audio_client_socket.close()
audio_stream.stop_stream()
audio_stream.close()
p.terminate()
