import time
import pyautogui
from pyjoycon import device
from pyjoycon.joycon import JoyCon

# Set up JoyCon
id = device.get_L_id()
joycon = JoyCon(*id)

is_pressed = False

prev_z_acc = 0
threshold = 500

while True:
    z_acc = joycon.get_status()["accel"]["z"]
    print(z_acc)

    # skip first iteration
    if prev_z_acc == 0:
        prev_z_acc = z_acc
        continue 

    diff = abs(z_acc - prev_z_acc)
    if diff > threshold and not is_pressed:
        is_pressed = True
        print(is_pressed)
        pyautogui.keyDown('s')
    elif diff <= threshold and is_pressed:
        is_pressed = False
        print(is_pressed)
        pyautogui.keyUp('s')
    else:
        print("no change ", is_pressed)
    
    prev_z_acc = z_acc

    time.sleep(0.1)
