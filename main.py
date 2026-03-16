import ujson
import utime
import _thread
from usr.modbus_plc import write_plc_output, modbus_sensors_data
from usr.noise_sensor import read_noise_db
from umqtt import MQTTClient
import checkNet
from usr.device_credentials import setup_device_credentials
from usr.app_ota import run_app_ota
from misc import Power
import log
import modem
import sim
import ql_fs
from machine import WDT

# ========== Global State ==========
desired_temp = 35
diluted_filling_level = 800
concentration_level = 400
filling_mode_active = False
auto_mode_active = False
sensor_priority = "none"
gpio_state = {1: False, 2: False, 3: False}

# ========== MQTT Setup ==========
file_name = "/usr/config/current_cycle_count.json"
PROJECT_NAME = "New Leaf IoT 2.0"
PROJECT_VERSION = "1.0.0"
checknet = checkNet.CheckNetwork(PROJECT_NAME, PROJECT_VERSION)
data_dev = setup_device_credentials()
server = "mqtt.thingsboard.cloud"
port = 1883
device_id = data_dev['device_id']
user = device_id
password = data_dev['password']
print("Client ID: {}, Username: {}, Password: {}" .format(device_id, device_id, password))

# device_id = "NLDT_2532025_1687322"
# user = "NLDT_2532025_1687322"
# password = "newleaf_168732"

TOPIC_PUB = "v1/devices/me/telemetry"
TOPIC_SUB = "v1/devices/me/rpc/request/+"
TOPIC_SUB_ATTRIB = "v1/devices/me/attributes"
wdt = WDT(120)
log.basicConfig(level=log.INFO)
mqtt_log = log.getLogger("MQTT")

# ========== Control Functions (from JSON) ==========
def filling_mode(state):
    write_plc_output(8, state)
    write_plc_output(1, state)

def desiccant_cooling(state):
    if state == 1:
        write_plc_output(1, state)
        utime.sleep(1)
        write_plc_output(4, state)
    else:
        write_plc_output(4, state)
        utime.sleep(1)
        write_plc_output(1, state)

def air_chilling(state):
    if state == 1:
        write_plc_output(0, state)
        write_plc_output(5, state)
        write_plc_output(6, state)
        utime.sleep(1)
        write_plc_output(4, state)
    else:
        write_plc_output(4, state)
        utime.sleep(1)
        write_plc_output(0, state)
        write_plc_output(5, state)
        write_plc_output(6, state)

def desiccant_emptying(state):
    if state == 1:
        write_plc_output(7, state)
        utime.sleep(1)
        write_plc_output(4, state)
    else:
        write_plc_output(4, state)
        utime.sleep(1)
        write_plc_output(7, state)

def cooling_tower(state):
    write_plc_output(11, state)
    write_plc_output(12, state)

def auto_mode(state):
    global auto_mode_active
    auto_mode_active = bool(state)
    step = 0
    filling_started = False
    conc_started = False
    cooling_started = False
    emptying_started = False

    if state == 0:
        print("Turning off Auto mode...")
        write_plc_output(0, 0)
        write_plc_output(1, 0)
        write_plc_output(2, 0)
        write_plc_output(3, 0)
        write_plc_output(4, 0)
        write_plc_output(5, 0)
        auto_mode_active = False
        return

    while auto_mode_active:
        try:
            data = get_sensors_data()
            water_level = data.get("water_level")
            temp = data.get("dessicant_hot_out")
            if step == 0 and water_level <= diluted_filling_level:
                if not filling_started:
                    write_plc_output(4, 1)
                    filling_started = True
                    print("Step 0 Started")
            elif step == 0 and water_level > diluted_filling_level:
                write_plc_output(4, 0)
                filling_started = False
                step = 1
                print("Step 0 Completed")
            elif step == 1 and water_level > concentration_level:
                if not conc_started:
                    concentration(1)
                    conc_started = True
                    print("Step 1 Started")
            elif step == 1 and water_level <= concentration_level:
                concentration(0)
                conc_started = False
                step = 2
                print("Step 1 Completed")

            elif step == 2 and temp > desired_temp:
                if not cooling_started:
                    cooling(1)
                    cooling_started = True
                    print("Step 2 Started")
            elif step == 2 and temp <= desired_temp:
                cooling(0)
                cooling_started = False
                step = 3
                print("Step 2 Completed")

            elif step == 3 and water_level > 5:
                if not emptying_started:
                    emptying(1)
                    emptying_started = True
                    print("Step 3 Started")
            elif step == 3 and water_level <= 5:
                emptying(0)
                emptying_started = False
                step = 0
                print("Step 3 Completed")
            utime.sleep(1.7)
        except Exception as e:
            print("Auto mode error:", e)

def functional_control(pin, state):
    if pin == 100:
        filling_mode(state)
    elif pin == 101:
        desiccant_cooling(state)
    elif pin == 102:
        air_chilling(state)
    elif pin == 103:
        desiccant_emptying(state)
    elif pin == 104:
        cooling_tower(state)
    elif pin == 105:
        _thread.start_new_thread(auto_mode, (state,))

# ========== JSON Command Thread ==========
def input_thread():
    while True:
        try:
            json_cmd = input("JSON GPIO Command: ").strip()
            data = ujson.loads(json_cmd)
            pin = data.get("pin")
            state = data.get("state")
            if pin is not None and state in [0, 1]:
                if pin >= 100:
                    functional_control(pin, state)
                else:
                    write_plc_output(pin, state)
            else:
                print("Invalid JSON format")
        except Exception as e:
            print("Input thread error:", e)

# ========== MQTT Functions ==========
def get_gpio_status():
    return ujson.dumps(gpio_state)

def set_gpio_status(pin, status):
    gpio_state[pin] = status
    if pin == 1 and status:
        print("OTA Firmware update")
    elif pin == 2 and status:
        run_app_ota()
    elif pin == 3 and status:
        Power.powerRestart()

def on_connect(client):
    mqtt_log.info("Connected to MQTT broker")
    imei = modem.getDevImei()
    sim_no = sim.getPhoneNumber()
    count_data = ql_fs.read_json(file_name)
    # start_log = {"started_at": "started", "machine_id": count_data['machine_id'], "sim_no": sim_no, 'imei_number': imei}
    client.subscribe(TOPIC_SUB)
    client.publish(TOPIC_SUB_ATTRIB, get_gpio_status())
    # client.publish(TOPIC_PUB, ujson.dumps(start_log))

def on_message(topic, msg):
    try:
        message = ujson.loads(msg.decode())
        method = message.get("method")
        if method == "getGpioStatus":
            response = get_gpio_status()
            client.publish(topic.replace(b'request', b'response'), response)
        elif method == "setGpioStatus":
            params = message.get("params", {})
            pin = params.get("pin")
            enabled = params.get("enabled")
            if pin is not None:
                set_gpio_status(pin, enabled)
                response = get_gpio_status()
                client.publish(topic.replace(b'request', b'response'), response)
    except Exception as e:
        mqtt_log.error("MQTT message error: {}".format(e))

def publish_data():
    global sensor_priority
    while True:
        try:
            data = modbus_sensors_data()
            json_string = ujson.dumps(data)
            client.publish(TOPIC_PUB, json_string)
            mqtt_log.info("Published topic: {} with data: {}".format(TOPIC_PUB, json_string))
            utime.sleep(30)
            wdt.feed()
        except Exception as e:
            mqtt_log.error("Publish error: {}".format(e))


def subscribe_messages():
    while True:
        try:
            client.check_msg()
            utime.sleep(0.1)
            wdt.feed()
        except Exception as e:
            mqtt_log.error("Subscribe error: {}".format(e))

# ========== Main ==========
if __name__ == "__main__":
    checknet.poweron_print_once()
    stagecode, subcode = checknet.wait_network_connected(30)
    if stagecode == 3 and subcode == 1:
        client = MQTTClient(client_id=device_id, server=server, port=port, user=user, password=password)
        client.set_callback(on_message)
        client.connect(clean_session=False)
        on_connect(client)

        _thread.start_new_thread(input_thread, ())
        _thread.start_new_thread(publish_data, ())
        _thread.start_new_thread(subscribe_messages, ())

        while True:
            utime.sleep(5)
            wdt.feed()
    else:
        print("Network connection failed: Stage {}, Subcode {}".format(stagecode, subcode))
