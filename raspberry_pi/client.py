import socket

HOST = '192.168.10.2'  # IP Mini PC
PORT = 5000

try:
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.connect((HOST, PORT))
		s.sendall(b'Buka Camera Sekarang')
		print("Arahan Berjaya Dihantar")
except Exception as e:
	print(f"Gagal Sambung: {e}")
