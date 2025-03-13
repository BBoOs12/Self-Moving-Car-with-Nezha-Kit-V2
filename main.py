import asyncio
from bleak import BleakClient, BleakScanner
from flask import Flask, jsonify, render_template

# MAC Address του Micro:bit
MICROBIT_MAC = "E8:B7:F1:6E:38:E4"

# UUIDs για Bluetooth UART
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
RX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# Αποθήκευση δεδομένων αισθητήρων
sensor_data = {"distance": 0, "crash": 0}

# Flask Web Server
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")  # Σελίδα HTML

@app.route('/data')
def get_data():
    return jsonify(sensor_data)  # Επιστροφή δεδομένων σε JSON

# Συνάρτηση για ανάγνωση δεδομένων από το Micro:bit
async def notification_handler(sender, data):
    global sensor_data
    message = data.decode("utf-8").strip()
    
    if message.startswith("DIST:"):
        sensor_data["distance"] = int(message.split(":")[1])
    elif message.startswith("CRASH:"):
        sensor_data["crash"] = int(message.split(":")[1])

    print(f"📡 Νέο Δεδομένο: {sensor_data}")

# Σύνδεση στο Micro:bit
async def connect_to_microbit():
    while True:
        try:
            print(f"🔄 Προσπάθεια σύνδεσης στο Micro:bit ({MICROBIT_MAC})...")
            async with BleakClient(MICROBIT_MAC) as client:
                if not client.is_connected:
                    print("❌ Αποτυχία σύνδεσης! Προσπάθεια ξανά...")
                    await asyncio.sleep(5)
                    continue
                
                print(f"✅ Συνδέθηκε στο Micro:bit ({MICROBIT_MAC})")
                await client.start_notify(RX_CHARACTERISTIC_UUID, notification_handler)

                while True:
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"⚠️ Σφάλμα: {e}")
            await asyncio.sleep(5)  # Επανασύνδεση

# Εκκίνηση Flask & Bluetooth
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(connect_to_microbit())  # Σύνδεση στο Micro:bit
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)  # Εκκίνηση Flask
