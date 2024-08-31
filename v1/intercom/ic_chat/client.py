import socket
import cv2
import numpy as np
import pyaudio
import threading
import tkinter as tk
from tkinter import scrolledtext

# Set up the video client socket
video_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
video_client_socket.connect(('127.0.0.1', 9999))

# Set up the audio client socket
audio_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
audio_client_socket.connect(('127.0.0.1', 10000))

# Set up the chat client socket
chat_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_client_socket.connect(('127.0.0.1', 10001))

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

def receive_chat():
    while True:
        message = chat_client_socket.recv(1024).decode()
        if not message:
            break
        chat_display.insert(tk.END, f"Server: {message}\n")

def send_chat():
    message = chat_input.get()
    chat_input.delete(0, tk.END)
    chat_display.insert(tk.END, f"Client: {message}\n")
    chat_client_socket.sendall(message.encode())

# Tkinter chat window setup
def start_chat_window():
    global chat_display, chat_input
    root = tk.Tk()
    root.title("Client Chat")

    chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD)
    chat_display.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    chat_input = tk.Entry(root, width=50)
    chat_input.pack(padx=10, pady=10, fill=tk.X)
    chat_input.bind("<Return>", lambda event: send_chat())

    root.mainloop()

# Start the chat window in a separate thread
chat_thread = threading.Thread(target=start_chat_window)
chat_thread.start()

# Start audio receiving thread
audio_thread = threading.Thread(target=receive_audio)
audio_thread.start()

# Start chat receiving thread
chat_receive_thread = threading.Thread(target=receive_chat)
chat_receive_thread.start()

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
chat_client_socket.close()
audio_stream.stop_stream()
audio_stream.close()
p.terminate()
