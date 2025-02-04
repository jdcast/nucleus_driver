#!/usr/bin/env python3
"""
run_record.py

This script starts a ROS 2 bag recording process (recording all topics) and then
connects to a Nortek Nucleus DVL (via serial or TCP). It sends a command to enable AHRS output,
starts the DVL streaming, and then runs indefinitely until you interrupt it (Ctrl+C).

Upon exit, the script stops the DVL streaming, disconnects, and gracefully stops the bag recorder.
"""

import subprocess
import signal
import os
import logging
import time
import sys
from argparse import ArgumentParser
from datetime import datetime

import rclpy
from rclpy.executors import SingleThreadedExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import client classes (ensure these modules are in your PYTHONPATH)
from nucleus_clients.command import ClientCommand
from nucleus_clients.connect_serial import ClientConnectSerial
from nucleus_clients.connect_tcp import ClientConnectTcp
from nucleus_clients.disconnect import ClientDisconnect
from nucleus_clients.start import ClientStart
from nucleus_clients.stop import ClientStop


class NucleusCommunication:
	def command(self, command: str):
		client = ClientCommand()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(command=command, timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.reply

	def start(self):
		client = ClientStart()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.reply

	def stop(self):
		client = ClientStop()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.reply

	def connect_serial(self, serial_port: str):
		client = ClientConnectSerial()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(serial_port=serial_port, timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.status

	def connect_tcp(self, hostname: str, password: str):
		client = ClientConnectTcp()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(host=hostname, password=password, timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.status

	def disconnect(self):
		client = ClientDisconnect()
		executor = SingleThreadedExecutor()
		executor.add_node(client)
		response = client.send_request(timeout_sec=1)
		executor.shutdown()
		client.destroy_node()
		return response.status


# Define a custom SIGINT handler that simply raises KeyboardInterrupt.
def custom_sigint_handler(sig, frame):
	raise KeyboardInterrupt


def main():
	parser = ArgumentParser()
	parser.add_argument('-s', '--serial_port', help='Serial port for connection (e.g., /dev/ttyUSB0)')
	parser.add_argument('-n', '--hostname', help='Hostname for TCP connection')
	parser.add_argument('-p', '--password', help='Password for TCP connection')
	args = parser.parse_args()

	if args.serial_port is None and args.hostname is None:
		logging.error("You must specify either --serial_port or --hostname")
		sys.exit(1)

	if args.hostname is not None and args.password is None:
		logging.error("For TCP connection, --password must be specified")
		sys.exit(1)

	# Create a timestamped bag directory. For example, if mapping host directory to /data:
	timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
	bag_output_dir = f"/data/nucleus_dvl_{timestamp}"

	# Start ros2 bag recording as a subprocess.
	# This records all topics (-a) and writes the bag into the timestamped directory.
	bag_cmd = ["ros2", "bag", "record", "-a", "-o", bag_output_dir]
	bag_proc = subprocess.Popen(bag_cmd, start_new_session=True) # new session necessary so that bagging is stopped when script is killed vs waiting for when container is killed
	logging.info("Started ros2 bag recording with directory %s (PID: %s)", bag_output_dir, bag_proc.pid)

	# Initialize ROS 2.
	rclpy.init(args=sys.argv)
	# Immediately override the SIGINT handler so our handler is used. Necessary so that bagging is stopped when script is killed vs waiting for when container is killed
	signal.signal(signal.SIGINT, custom_sigint_handler)

	nucleus = NucleusCommunication()

	# Connect to the DVL using either serial or TCP.
	if args.serial_port:
		status = nucleus.connect_serial(args.serial_port)
		logging.info("Serial connection status: %s", status)
	else:
		status = nucleus.connect_tcp(args.hostname, args.password)
		logging.info("TCP connection status: %s", status)

	# Send commands to enable DVL functionality.
	response_setnav = nucleus.command('SETNAV,FREQ=10,DS="ON"')																																															   
	response_setahrs = nucleus.command('SETAHRS,FREQ=10,DS="ON"')																																														   
	response_setbt = nucleus.command('SETBT,WT="ON",DS="ON"')																																															   
	response_setalti = nucleus.command('SETALTI,DS="ON"s')																																																   
	response_setcurprof = nucleus.command('SETCURPROF,DS="ON"')																																															   
	response_settrig = nucleus.command('SETTRIG,SRC="INTERNAL",FREQ=2,ALTI=2,CP=2')																																										   
	response_setimu = nucleus.command('SETIMU,DS="ON"')																																																	   
	response_setmag = nucleus.command('SETMAG,DS="ON"')																																																	   
																																																																					  
	assert "OK" in response_setnav
	assert "OK" in response_setahrs
	assert "OK" in response_setbt
	assert "OK" in response_setalti
	assert "OK" in response_setcurprof
	assert "OK" in response_settrig
	assert "OK" in response_setimu
	assert "OK" in response_setmag

	# Start DVL streaming.
	reply = nucleus.start()
	logging.info("Start reply: %s", reply)

	logging.info("DVL is streaming and bag recording is active. Press Ctrl+C to exit.")

	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		logging.info("Exiting on user request...")

	# Since we've disabled the automatic shutdown signal,
	# we can now safely call our stop/disconnect commands.
	try:
		reply = nucleus.stop()
		logging.info("Stop reply: %s", reply)
	except Exception as e:
		logging.error("Error during stop: %s", e)

	try:
		status = nucleus.disconnect()
		logging.info("Disconnect status: %s", status)
	except Exception as e:
		logging.error("Error during disconnect: %s", e)

	# Shutdown bag recording gracefully by sending SIGINT to its process group.
	os.killpg(bag_proc.pid, signal.SIGINT)
	bag_proc.wait()
	logging.info("ros2 bag recording terminated.")

	rclpy.shutdown()


if __name__ == '__main__':
	main()
