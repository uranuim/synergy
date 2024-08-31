import socket
import cv2
import numpy as np
import pyaudio
import threading

# Video streaming server setup
video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_socket.bind(('0.0.0.0', 9000))
video_socket.listen(1)

# Audio streaming server setup
audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_socket.bind(('0.0.0.0', 11000))
audio_socket.listen(1)

print("Server listening for video on port 9000 and audio on port 11000...")

# Accept video and audio connections
video_client_socket, video_client_address = video_socket.accept()
audio_client_socket, audio_client_address = audio_socket.accept()

print(f"Video connection accepted from {video_client_address}")
print(f"Audio connection accepted from {audio_client_address}")

# Initialize the webcam with reduced resolution and frame rate
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Reduce resolution width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)  # Reduce resolution height
cap.set(cv2.CAP_PROP_FPS, 15)  # Reduce frame rate

# Initialize audio stream
p = pyaudio.PyAudio()
audio_stream = p.open(format=pyaudio.paInt16,
                      channels=1,
                      rate=44100,
                      input=True,
                      frames_per_buffer=1024)

def send_audio():
    while True:
        audio_data = audio_stream.read(1024)
        audio_client_socket.sendall(audio_data)

# Start audio streaming thread
audio_thread = threading.Thread(target=send_audio)
audio_thread.start()

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Encode the frame with lower quality
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]  # Adjust quality parameter (lower value means more compression)
    _, buffer = cv2.imencode('.jpg', frame, encode_param)
    buffer = buffer.tobytes()

    # Send the length of the frame first
    video_client_socket.sendall(len(buffer).to_bytes(4, byteorder='big'))
    
    # Send the frame itself
    video_client_socket.sendall(buffer)

    # Display the frame being sent (for debugging purposes)
    cv2.imshow('Server - Sending Video', frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
video_client_socket.close()
audio_client_socket.close()
video_socket.close()
audio_socket.close()
audio_stream.stop_stream()
audio_stream.close()
p.terminate()
