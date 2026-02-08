import requests
import subprocess
import time
import threading

# 🔴 PUT YOUR BOT TOKEN HERE
TOKEN = "8020390884:AAEkzEUBNy1gixWPX2WA_Xb32QvPuV-LyqE"
API = f"https://api.telegram.org/bot{TOKEN}"

last_update_id = 0


def send(chat_id, text):
    for i in range(0, len(text), 3500):
        requests.post(
            f"{API}/sendMessage",
            json={"chat_id": chat_id, "text": text[i:i+3500]}
        )


def stream_process(chat_id, process):
    buffer = ""
    last_flush = time.time()

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        if line:
            buffer += line

        # flush every 0.5 seconds
        if time.time() - last_flush >= 0.5 and buffer:
            send(chat_id, buffer)
            buffer = ""
            last_flush = time.time()

    if buffer.strip():
        send(chat_id, buffer)

    send(chat_id, f"[exit code {process.returncode}]")


print("Bot started (polling, continuous sync every 0.5s)...")

while True:
    try:
        resp = requests.get(
            f"{API}/getUpdates",
            params={"offset": last_update_id + 1, "timeout": 30},
            timeout=35
        ).json()

        if not resp.get("ok"):
            time.sleep(2)
            continue

        for update in resp["result"]:
            last_update_id = update["update_id"]

            msg = update.get("message")
            if not msg:
                continue

            chat_id = msg["chat"]["id"]
            text = msg.get("text")
            if not text:
                continue

            send(chat_id, f"$ {text}")

            try:
                process = subprocess.Popen(
                    text,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                # run streamer in same thread (sync behavior)
                stream_process(chat_id, process)

            except Exception as e:
                send(chat_id, f"ERROR: {e}")

    except Exception as e:
        print("Main loop error:", e)
        time.sleep(5)
