import asyncio
from flask import Flask, jsonify
from bleak import BleakClient, BleakScanner, BleakError

# 🔹 Αυτόματη εύρεση του Micro:bit (αν δεν ξέρεις τη MAC)
AUTO_DETECT = False
MICROBIT_MAC = "E8:B7:F1:6E:38:E4"  # Βάλε τη σωστή MAC αν δεν κάνεις αυτόματη ανίχνευση

# 🔹 Bluetooth UUIDs για UART
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
RX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# 🔹 Αποθήκευση δεδομένων αισθητήρων
sensor_data = {"distance": "N/A", "crash": "N/A"}

# 🔹 Flask Server
app = Flask(__name__)

@app.route("/")
def home():
    """Απλή ιστοσελίδα για εμφάνιση δεδομένων."""
    return f"""
    <html>
    <head><title>Micro:bit Sensor Data</title></head>
    <body>
        <h1>🔹 Micro:bit Sensor Data 🔹</h1>
        <p>📏 Απόσταση: <strong>{sensor_data["distance"]} cm</strong></p>
        <p>💥 Σύγκρουση: <strong>{sensor_data["crash"]}</strong></p>
        <p><a href='/data'>🔍 Δεδομένα JSON</a></p>
    </body>
    </html>
    """

@app.route("/data")
def get_data():
    """Επιστροφή δεδομένων σε JSON."""
    return jsonify(sensor_data)

async def find_microbit():
    """Αυτόματη ανίχνευση της MAC του Micro:bit."""
    print("🔍 Σάρωση για Micro:bit...")
    devices = await BleakScanner.discover()
    for device in devices:
        if "BBC micro:bit" in device.name:
            print(f"✅ Βρέθηκε Micro:bit: {device.address}")
            return device.address
    print("❌ Δεν βρέθηκε Micro:bit.")
    return None

async def connect_to_microbit():
    """Σύνδεση στο Micro:bit και λήψη δεδομένων μέσω Bluetooth UART."""
    global MICROBIT_MAC
    if AUTO_DETECT:
        MICROBIT_MAC = await find_microbit()
        if not MICROBIT_MAC:
            return
    
    while True:
        print(f"🔄 Προσπάθεια σύνδεσης στο Micro:bit ({MICROBIT_MAC})...")
        try:
            async with BleakClient(MICROBIT_MAC) as client:
                if not client.is_connected:
                    print("❌ Απέτυχε η σύνδεση!")
                    continue

                print(f"✅ Συνδέθηκε στο Micro:bit ({MICROBIT_MAC})")

                async def notification_handler(sender, data):
                    """Λήψη και αποθήκευση δεδομένων από Micro:bit."""
                    message = data.decode("utf-8").strip()
                    print(f"📡 Λήφθηκε: {message}")

                    # 🔹 Ανάλυση δεδομένων
                    if message.startswith("DIST:"):
                        sensor_data["distance"] = message.split(":")[1]
                    elif message.startswith("CRASH:"):
                        sensor_data["crash"] = "ΝΑΙ" if message.split(":")[1] == "1" else "ΟΧΙ"

                await client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)

                # ✅ Συνδέθηκε, κράτα τη σύνδεση ενεργή
                while client.is_connected:
                    await asyncio.sleep(1)

        except BleakError as e:
            print(f"⚠️ Σφάλμα: {e}")
        
        print("🔁 Προσπάθεια επανασύνδεσης σε 5 δευτερόλεπτα...")
        await asyncio.sleep(1)

async def main():
    """Τρέχει τον Flask Server και τη Bluetooth σύνδεση ταυτόχρονα."""
    task1 = asyncio.create_task(connect_to_microbit())
    task2 = asyncio.to_thread(app.run, host="0.0.0.0", port=5000, debug=True, use_reloader=False)

    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    asyncio.run(main())
