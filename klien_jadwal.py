#!/usr/bin/env python3
"""Klien cek jadwal: python3 klien_jadwal.py JADWAL USA-WP2260110"""
import socket, sys, time
HOST, PORT = "127.0.0.1", 5050
def kirim(perintah):
    t0 = time.perf_counter()
    with socket.create_connection((HOST, PORT), timeout=3) as s:
        s.sendall(perintah.encode())
        balasan = s.recv(2048).decode().strip()
    return balasan, (time.perf_counter() - t0) * 1000
if __name__ == "__main__":
    perintah = " ".join(sys.argv[1:]) or "JADWAL USA-WP2260110"
    b, ms = kirim(perintah)
    print(f"> {perintah}\n< {b}\n  (waktu bolak-balik {ms:.2f} ms)")
