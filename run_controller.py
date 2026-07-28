import argparse
import ctypes
import os
import time
from ctypes import wintypes

import serial
from serial.tools import list_ports

DEFAULT_PORT = os.environ.get("CONTROLLER_PORT", "COM3")
DEFAULT_BAUD_RATE = int(os.environ.get("CONTROLLER_BAUD_RATE", "9600"))
DEFAULT_DURATION_SECONDS = int(os.environ.get("CONTROLLER_DURATION_SECONDS", str(30 * 60)))
DEFAULT_WAIT_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLER_WAIT_TIMEOUT_SECONDS", "0"))
DEFAULT_BACKEND = os.environ.get("CONTROLLER_BACKEND", "auto")
DEFAULT_LEFT_MOTOR = int(os.environ.get("CONTROLLER_LEFT_MOTOR", "100"))
DEFAULT_RIGHT_MOTOR = int(os.environ.get("CONTROLLER_RIGHT_MOTOR", "100"))
DEFAULT_REFRESH_INTERVAL_SECONDS = float(os.environ.get("CONTROLLER_REFRESH_INTERVAL_SECONDS", "0.25"))

ERROR_SUCCESS = 0
ERROR_DEVICE_NOT_CONNECTED = 1167


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


class XINPUT_VIBRATION(ctypes.Structure):
    _fields_ = [
        ("wLeftMotorSpeed", wintypes.WORD),
        ("wRightMotorSpeed", wintypes.WORD),
    ]


def positive_int(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return number


def percent(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if number < 0 or number > 100:
        raise argparse.ArgumentTypeError("value must be from 0 to 100")
    return number


def positive_float(value):
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than 0")
    return number


def controller_index(value):
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a number") from exc
    if number < 0 or number > 3:
        raise argparse.ArgumentTypeError("controller index must be from 0 to 3")
    return number


def available_ports():
    return [port.device for port in list_ports.comports()]


def load_xinput():
    for dll_name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            return ctypes.WinDLL(dll_name)
        except OSError:
            pass
    return None


def connected_xinput_controllers(xinput=None):
    xinput = xinput or load_xinput()
    if not xinput:
        return []

    connected = []
    for index in range(4):
        state = XINPUT_STATE()
        result = xinput.XInputGetState(index, ctypes.byref(state))
        if result == ERROR_SUCCESS:
            connected.append(index)
    return connected


def parse_args():
    parser = argparse.ArgumentParser(description="Run vibration using either a serial controller or an Xbox/XInput controller.")
    parser.add_argument(
        "--backend",
        choices=("auto", "serial", "xinput"),
        default=DEFAULT_BACKEND,
        help=f"Controller backend. Default: {DEFAULT_BACKEND}",
    )
    parser.add_argument("--port", default=DEFAULT_PORT, help=f"Serial port to use. Default: {DEFAULT_PORT}")
    parser.add_argument("--baud-rate", type=positive_int, default=DEFAULT_BAUD_RATE, help=f"Baud rate. Default: {DEFAULT_BAUD_RATE}")
    parser.add_argument(
        "--duration",
        type=positive_int,
        default=DEFAULT_DURATION_SECONDS,
        help=f"How long to keep the motor on, in seconds. Default: {DEFAULT_DURATION_SECONDS}",
    )
    parser.add_argument("--auto-port", action="store_true", help="Use the first detected serial port instead of the configured port.")
    parser.add_argument(
        "--wait-port",
        nargs="?",
        const=DEFAULT_WAIT_TIMEOUT_SECONDS,
        type=int,
        metavar="SECONDS",
        help="Wait for a serial port to appear. Use 0 to wait forever.",
    )
    parser.add_argument("--list-ports", action="store_true", help="Show detected serial ports and exit.")
    parser.add_argument("--list-controllers", action="store_true", help="Show detected Xbox/XInput controllers and exit.")
    parser.add_argument("--controller-index", type=controller_index, help="Xbox/XInput controller index from 0 to 3. Default: first connected controller.")
    parser.add_argument("--left-motor", type=percent, default=DEFAULT_LEFT_MOTOR, help=f"Left/low-frequency motor strength 0-100. Default: {DEFAULT_LEFT_MOTOR}")
    parser.add_argument("--right-motor", type=percent, default=DEFAULT_RIGHT_MOTOR, help=f"Right/high-frequency motor strength 0-100. Default: {DEFAULT_RIGHT_MOTOR}")
    parser.add_argument(
        "--refresh-interval",
        type=positive_float,
        default=DEFAULT_REFRESH_INTERVAL_SECONDS,
        help=f"Seconds between repeated XInput vibration commands. Default: {DEFAULT_REFRESH_INTERVAL_SECONDS}",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the serial commands without opening a port.")
    return parser.parse_args()


def wait_seconds(seconds):
    deadline = time.monotonic() + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, 1))


def write_command(ser, command, dry_run=False):
    line = f"{command}\n"
    print(f"Sending: {line.strip()}")
    if not dry_run:
        ser.write(line.encode("ascii"))


def motor_speed(percent_value):
    return int(65535 * (percent_value / 100))


def set_xinput_vibration(xinput, controller, left_percent, right_percent):
    vibration = XINPUT_VIBRATION(motor_speed(left_percent), motor_speed(right_percent))
    return xinput.XInputSetState(controller, ctypes.byref(vibration))


def resolve_port(requested_port, auto_port=False, wait_port=None):
    start = time.monotonic()
    announced_wait = False

    while True:
        ports = available_ports()
        if auto_port and ports:
            return ports[0], ports
        if requested_port in ports:
            return requested_port, ports
        if not auto_port and not ports:
            # Let serial.Serial produce the normal OS error unless the user asked to wait.
            if wait_port is None:
                return requested_port, ports
        elif not auto_port:
            return requested_port, ports

        if wait_port is None:
            return requested_port, ports

        elapsed = time.monotonic() - start
        if wait_port > 0 and elapsed >= wait_port:
            return requested_port, ports

        if not announced_wait:
            target = "any serial port" if auto_port else requested_port
            timeout_text = "forever" if wait_port == 0 else f"up to {wait_port} seconds"
            print(f"Waiting for {target} {timeout_text}...")
            announced_wait = True
        time.sleep(1)


def choose_backend(args, ports, xinput_controllers):
    if args.backend != "auto":
        return args.backend
    if xinput_controllers:
        return "xinput"
    if ports:
        return "serial"
    return "serial"


def run_xinput(args, xinput, controllers):
    if not xinput:
        print("XInput is not available on this Windows installation.")
        return 1
    if not controllers:
        print("No Xbox/XInput controllers detected.")
        return 1

    controller = args.controller_index if args.controller_index is not None else controllers[0]
    if controller not in controllers:
        print(f"Xbox/XInput controller {controller} is not connected. Connected controllers: {', '.join(map(str, controllers))}")
        return 1

    if args.dry_run:
        print(
            "Dry run: would vibrate Xbox/XInput controller "
            f"{controller} for {args.duration} seconds "
            f"(left={args.left_motor}%, right={args.right_motor}%, refresh={args.refresh_interval}s)."
        )
        return 0

    try:
        print(
            f"Vibration ON: controller {controller}, "
            f"left={args.left_motor}%, right={args.right_motor}%, "
            f"duration={args.duration}s, refresh={args.refresh_interval}s"
        )
        deadline = time.monotonic() + args.duration
        while True:
            result = set_xinput_vibration(xinput, controller, args.left_motor, args.right_motor)
            if result != ERROR_SUCCESS:
                print(f"XInput error refreshing vibration: {result}")
                return 1

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return 0
            time.sleep(min(remaining, args.refresh_interval))
        return 0
    except KeyboardInterrupt:
        print("Stopped manually. Turning vibration OFF...")
        return 130
    finally:
        result = set_xinput_vibration(xinput, controller, 0, 0)
        print("Vibration OFF")
        if result not in (ERROR_SUCCESS, ERROR_DEVICE_NOT_CONNECTED):
            print(f"XInput error stopping vibration: {result}")


def run_serial(args, port, ports):
    if args.dry_run:
        print(f"Dry run: would use {port} at {args.baud_rate} baud for {args.duration} seconds.")
        write_command(None, "ON", dry_run=True)
        wait_seconds(args.duration)
        write_command(None, "OFF", dry_run=True)
        return 0

    if ports and port not in ports:
        print(f"Warning: {port} was not in the detected ports: {', '.join(ports)}")
    elif not ports:
        print("Warning: no serial ports were detected. Check the USB connection and driver if opening the port fails.")

    ser = None
    try:
        with serial.Serial(port, args.baud_rate, timeout=1) as ser:
            time.sleep(2)  # wait for controller reset

            print("Motor ON")
            write_command(ser, "ON")

            wait_seconds(args.duration)

            print("Motor OFF")
            write_command(ser, "OFF")
        return 0

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Tip: run `python run_controller.py --list-ports` to see available ports, then pass `--port COMx`.")
        print("Tip: for an Xbox-style USB controller, run `python run_controller.py --backend xinput --duration 10`.")
        return 1
    except KeyboardInterrupt:
        print("Stopped manually. Turning motor OFF...")
        if ser and ser.is_open:
            write_command(ser, "OFF")
        return 130


def main():
    args = parse_args()
    xinput = load_xinput()
    xinput_controllers = connected_xinput_controllers(xinput)

    if args.list_ports:
        ports = available_ports()
        if ports:
            print("Detected serial ports:")
            for port in ports:
                print(f"  {port}")
        else:
            print("No serial ports detected.")
        return 0

    if args.list_controllers:
        if xinput_controllers:
            print("Detected Xbox/XInput controllers:")
            for controller in xinput_controllers:
                print(f"  {controller}")
        else:
            print("No Xbox/XInput controllers detected.")
        return 0

    ports = available_ports()
    backend = choose_backend(args, ports, xinput_controllers)
    if backend == "xinput":
        return run_xinput(args, xinput, xinput_controllers)

    port, ports = resolve_port(args.port, args.auto_port, args.wait_port)
    return run_serial(args, port, ports)

if __name__ == "__main__":
    raise SystemExit(main())
