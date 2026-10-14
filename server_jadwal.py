#!/usr/bin/env python3
"""Server layanan cek jadwal kuliah (socket TCP) + pipe log akses ke pemroses log."""
import os, socket, sys, threading, time, signal

HOST, PORT = "127.0.0.1", 5050

JADWAL = {
    "USA-WP2260110": ("Sistem Operasi",        "Senin",  "08.00-10.30", "Lab 3"),
    "USA-WP2260120": ("Basis Data",            "Selasa", "10.00-12.30", "R. 2.04"),
    "USA-WP2260130": ("Jaringan Komputer",     "Rabu",   "13.00-15.30", "Lab 1"),
    "USA-WP2260140": ("Rekayasa Perangkat Lunak","Kamis", "08.00-10.30", "R. 3.01"),
    "USA-WP2260150": ("Pemrograman Web",       "Jumat",  "09.00-11.30", "Lab 2"),
}

def pemroses_log(fd_baca, berkas_log):
    """Proses anak: membaca log dari pipe, menyimpan ke berkas, merangkum saat pipe ditutup."""
    jumlah, per_status = 0, {}
    with os.fdopen(fd_baca, "r") as pipe, open(berkas_log, "w") as f:
        for baris in pipe:                       # blocking read pada ujung baca pipe
            f.write(baris); f.flush()
            jumlah += 1
            status = baris.split("|")[3]
            per_status[status] = per_status.get(status, 0) + 1
    print(f"[PEMROSES-LOG pid={os.getpid()}] EOF pipe. total={jumlah} per_status={per_status}", flush=True)

def proses_perintah(teks):
    bagian = teks.strip().split()
    if len(bagian) == 2 and bagian[0].upper() == "JADWAL":
        kode = bagian[1].upper()
        if kode in JADWAL:
            n, h, j, r = JADWAL[kode]
            return "OK", f"OK {kode} | {n} | {h} | {j} | {r}\n"
        return "NOTFOUND", f"ERR mata kuliah {kode} tidak ditemukan\n"
    if len(bagian) == 3 and bagian[0].upper() == "JADWAL" and bagian[1].upper() == "HARI":
        hari = bagian[2].capitalize()
        hasil = [f"{k} {v[0]} {v[2]} {v[3]}" for k, v in JADWAL.items() if v[1] == hari]
        if hasil:
            return "OK", "OK " + " ; ".join(hasil) + "\n"
        return "NOTFOUND", f"ERR tidak ada kuliah pada hari {hari}\n"
    return "BADCMD", "ERR perintah tidak dikenal. Gunakan: JADWAL <kode> | JADWAL HARI <hari>\n"

def layani(conn, addr, tulis_log, kunci):
    t0 = time.perf_counter()
    with conn:
        data = conn.recv(1024).decode().strip()
        status, balasan = proses_perintah(data)
        conn.sendall(balasan.encode())
    ms = (time.perf_counter() - t0) * 1000
    baris = f"{time.strftime('%H:%M:%S')}|{addr[0]}:{addr[1]}|{data}|{status}|{ms:.2f}ms\n"
    with kunci:                                  # serialisasi penulisan ke pipe antar thread
        tulis_log.write(baris); tulis_log.flush()

def main():
    berkas_log = sys.argv[1] if len(sys.argv) > 1 else "akses.log"
    r, w = os.pipe()                             # pipe anonim: w = ujung tulis, r = ujung baca
    pid = os.fork()
    if pid == 0:                                 # ---- proses anak = pemroses log
        os.close(w)
        pemroses_log(r, berkas_log)
        os._exit(0)
    os.close(r)                                  # ---- proses induk = server socket
    tulis_log = os.fdopen(w, "w")
    kunci = threading.Lock()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT)); srv.listen(16)
    print(f"[SERVER pid={os.getpid()}] mendengar di {HOST}:{PORT}; pemroses log pid={pid}", flush=True)

    berhenti = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: berhenti.set())
    srv.settimeout(0.5)
    while not berhenti.is_set():
        try:
            conn, addr = srv.accept()
        except socket.timeout:
            continue
        threading.Thread(target=layani, args=(conn, addr, tulis_log, kunci), daemon=True).start()
    time.sleep(0.3)
    srv.close(); tulis_log.close()               # menutup ujung tulis -> anak menerima EOF
    os.waitpid(pid, 0)
    print("[SERVER] berhenti.", flush=True)

if __name__ == "__main__":
    main()
