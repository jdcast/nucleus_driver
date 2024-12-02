import serial
import time

def main():
    port = '/dev/ttyUSB0'  # Replace with your serial port
    baudrate = 115200      # Replace with your device's baud rate
    log_file = "serial_log.txt"  # File to log messages

    ser = None
    with open(log_file, "a") as log:
        while ser is None:
            try:
                # Attempt to open the serial port
                ser = serial.Serial(port, baudrate, timeout=1)
                connection_message = f"Serial port {port} connected successfully at {time.ctime()}.\n"
                print(connection_message)
                log.write(connection_message)
                log.flush()  # Ensure the log is written immediately
            except serial.SerialException as e:
                retry_message = f"{time.ctime()}: Serial port {port} not available. Retrying in 2 seconds...\n"
                print(retry_message, end="")
                log.write(retry_message)
                log.flush()
                time.sleep(2)  # Wait before retrying

        try:
            # Listen for initialization output
            print("Waiting for device initialization message...")
            initialization_output = []
            while True:
                try:
                    # Read a line of data
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        initialization_output.append(data)
                        print(f"Received: {data}")
                        log.write(f"{time.ctime()}: {data}\n")
                        log.flush()
                        # Check if the initialization output is complete
                        if "OK" in data:
                            print("Device initialized successfully!")
                            print("Initialization Output:\n" + "\n".join(initialization_output))
                            log.write(f"{time.ctime()}: Device initialized successfully!\n")
                            break
                except serial.SerialException as e:
                    print(f"Serial exception: {e}")
                    break
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt detected. Exiting...")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break

            # Continue reading data after initialization
            print("Listening for additional data...")
            while True:
                try:
                    data = ser.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        print(f"Received: {data}")
                        log.write(f"{time.ctime()}: {data}\n")
                        log.flush()
                except KeyboardInterrupt:
                    print("\nKeyboardInterrupt detected. Exiting...")
                    break
                except Exception as e:
                    print(f"Unexpected error: {e}")
                    break
        finally:
            # Ensure the port is closed on exit
            if ser and ser.is_open:
                ser.close()
                disconnect_message = f"Serial port {port} closed at {time.ctime()}.\n"
                print(disconnect_message)
                log.write(disconnect_message)
                log.flush()

if __name__ == "__main__":
    main()
