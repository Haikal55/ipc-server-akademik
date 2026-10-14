#!/usr/bin/env python3
"""Uji: N klien serentak (thread) mengirim permintaan; hitung keberhasilan dan waktu."""
import sys, threading, time, random
from klien_jadwal import kirim
N = int(sys.argv[1]) if len(sys.argv) > 1 else 50
kode = ["USA-WP2260110","USA-WP2260120","USA-WP2260130","USA-WP2260140","USA-WP2260150"]
hasil, kunci = [], threading.Lock()
def kerja(i):
    try:
        b, ms = kirim(f"JADWAL {random.choice(kode)}")
        ok = b.startswith("OK")
    except Exception as e:
        ok, ms = False, 0
    with kunci: hasil.append((ok, ms))
t0 = time.perf_counter()
th = [threading.Thread(target=kerja, args=(i,)) for i in range(N)]
[t.start() for t in th]; [t.join() for t in th]
tot = time.perf_counter() - t0
ok = sum(1 for o,_ in hasil if o); ms = sorted(m for o,m in hasil if o)
print(f"klien={N} berhasil={ok} gagal={N-ok} total={tot*1000:.1f}ms rata2={sum(ms)/len(ms):.2f}ms maks={ms[-1]:.2f}ms")
