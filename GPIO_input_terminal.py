import ujson
import utime
import _thread
from usr.modbus_plc import write_plc_output, get_sensors_data

desired_temp = 35
diluted_filling_level = 800
concentration_level = 400
filling_mode_active = False  # Global flag for filling_mode
auto_mode_active = False  # Shared flag for auto mode

def filling_mode(state):
    global filling_mode_active

    if state == 0:
        print("[Filling Mode] Turning OFF.")
        filling_mode_active = False
        write_plc_output(4, 0)  # Stop filling immediately
        return

    print("[Filling Mode] Turning ON.")
    filling_mode_active = True
    filling_started = False
    loop_count = 0

    while filling_mode_active:
        try:
            data = get_sensors_data()
            loop_count += 1
            print(data)

            if not isinstance(data, dict):
                print("[Filling Mode] Warning: Invalid sensor data. Skipping...")
                utime.sleep(1)
                continue

            water_level = data.get("water_level")

            if water_level is not None:

                if water_level < diluted_filling_level:
                    if not filling_started:
                        print("[Filling Mode] Start Filling")
                        write_plc_output(4, 1)
                        filling_started = True

                elif water_level >= diluted_filling_level:
                    if filling_started:
                        print("[Filling Mode] Stop Filling")
                        write_plc_output(4, 0)
                        filling_started = False
                        # NOTE: Do not stop the mode here — allow manual stop
                        # filling_mode_active = False

            else:
                print("[Filling Mode] Warning: 'water_level' is None.")

        except Exception as e:
            print("[Filling Mode] Error:", e)

        utime.sleep(1)

    print("[Filling Mode] Stopped.")



def concentration(state):
    write_plc_output(0, state)
    write_plc_output(3, state)
    write_plc_output(5, state)
    return True

def cooling(state):
    write_plc_output(0, 0)
    write_plc_output(3, state)
    write_plc_output(1, state)

def emptying(state):
    write_plc_output(0, 0)
    write_plc_output(3, state)
    write_plc_output(1, 0)
    write_plc_output(2, state)

def cooling_tower(state):
    write_plc_output(6, state)
    write_plc_output(11, state)

def auto_mode(state):
    global auto_mode_active

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

    print("Auto mode ON")
    auto_mode_active = True
    start_step = 0
    filling_started = False
    concentration_started = False
    cooling_started = False
    emptying_started = False

    while auto_mode_active:
        try:
            data = get_sensors_data()
            water_level = data.get("water_level")
            temperature = data.get("dessicant_hot_out")
            # Step 1: Filling until water level >= 800
            if start_step == 0:
                if water_level is not None and water_level <= diluted_filling_level:
                    if not filling_started:
                        print("Step 1: Start Filling")
                        write_plc_output(4, 1)
                        filling_started = True
                elif water_level is not None and water_level >= diluted_filling_level:
                    if filling_started:
                        print("Step 1: Stop Filling")
                        write_plc_output(4, 0)
                        filling_started = False
                        start_step = 1

            # Step 2: Concentration until water level <= 300
            elif start_step == 1:
                if water_level is not None and water_level > concentration_level:
                    if not concentration_started:
                        print("Step 2: Start Concentration")
                        concentration(1)
                        concentration_started = True
                elif water_level is not None and water_level <= concentration_level:
                    if concentration_started:
                        print("Step 2: Stop Concentration")
                        concentration(0)
                        concentration_started = False
                        start_step = 2

            # Step 3: Cooling until temperature <= desired_temp
            elif start_step == 2:
                if temperature is not None and temperature > desired_temp:
                    if not cooling_started:
                        print("Step 3: Start Cooling")
                        cooling(1)
                        cooling_started = True
                elif temperature is not None and temperature <= desired_temp:
                    if cooling_started:
                        print("Step 3: Stop Cooling")
                        cooling(0)
                        cooling_started = False
                        start_step = 3

            # Step 4: Emptying until water level < 5
            elif start_step == 3:
                if water_level is not None and water_level > 5:
                    if not emptying_started:
                        print("Step 4: Start Emptying")
                        emptying(1)
                        emptying_started = True
                elif water_level is not None and water_level <= 5:
                    if emptying_started:
                        print("Step 4: Stop Emptying")
                        emptying(0)
                        emptying_started = False
                        start_step = 0  # Loop back to Step 1

        except Exception as e:
            print("Auto mode error:", e)

        utime.sleep(1)
    print("Auto mode stopped.")


# Functional control for special pins
def functional_control(pin, state):
    if pin == 100:
        _thread.start_new_thread(filling_mode, (state,))
    elif pin == 101:
        concentration(state)
    elif pin == 102:
        cooling(state)
    elif pin == 103:
        emptying(state)
    elif pin == 104:
        cooling_tower(state)
    elif pin == 105:
        _thread.start_new_thread(auto_mode, (state,))


# Command input thread
def input_thread():
    while True:
        try:
            json_cmd = input("JSON GPIO Command: ").strip()
            print("------------>:", json_cmd)

            # Parse the JSON string
            data = ujson.loads(json_cmd)
            pin = data.get("pin")
            state = data.get("state")

            # Validate and write
            if pin is not None and state in [0, 1]:
                if pin >= 100:
                    functional_control(pin, state)
                else:
                    write_plc_output(pin, state)
            else:
                print("Invalid JSON format! Expected keys: 'pin' (int), 'state' (0 or 1)")

        except Exception as e:
            print("Invalid input! Error:", e)


# Start threads
_thread.start_new_thread(input_thread, ())

# Keep main thread alive
while True:
    utime.sleep(10)
