import socket
import cv2
import numpy as np
import pyaudio
import threading
import tkinter as tk
from tkinter import scrolledtext

# Video streaming server setup
video_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_socket.bind(('0.0.0.0', 9999))
video_socket.listen(1)

# Audio streaming server setup
audio_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_socket.bind(('0.0.0.0', 10000))
audio_socket.listen(1)

# Chat server setup
chat_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_socket.bind(('0.0.0.0', 10001))
chat_socket.listen(1)

print("Server listening for video on port 9999, audio on port 10000, and chat on port 10001...")

# Accept video, audio, and chat connections
video_client_socket, video_client_address = video_socket.accept()
audio_client_socket, audio_client_address = audio_socket.accept()
chat_client_socket, chat_client_address = chat_socket.accept()

print(f"Video connection accepted from {video_client_address}")
print(f"Audio connection accepted from {audio_client_address}")
print(f"Chat connection accepted from {chat_client_address}")

# Initialize the webcam with reduced resolution
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

def receive_chat():
    while True:
        message = chat_client_socket.recv(1024).decode()
        if not message:
            break
        chat_display.insert(tk.END, f"Client: {message}\n")

def send_chat():
    message = chat_input.get()
    chat_input.delete(0, tk.END)
    chat_display.insert(tk.END, f"Server: {message}\n")
    chat_client_socket.sendall(message.encode())

# Tkinter chat window setup
def start_chat_window():
    global chat_display, chat_input
    root = tk.Tk()
    root.title("Server Chat")

    chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    chat_input = tk.Entry(root, width=50)
    chat_input.pack(padx=10, pady=10, fill=tk.X)
    chat_input.bind("<Return>", lambda event: send_chat())

    root.mainloop()

# Start the chat window in a separate thread
chat_thread = threading.Thread(target=start_chat_window)
chat_thread.start()

# Start audio streaming thread
audio_thread = threading.Thread(target=send_audio)
audio_thread.start()

# Start chat receiving thread
chat_receive_thread = threading.Thread(target=receive_chat)
chat_receive_thread.start()

# Video streaming loop
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
chat_client_socket.close()
video_socket.close()
audio_socket.close()
chat_socket.close()
audio_stream.stop_stream()
audio_stream.close()
p.terminate()
