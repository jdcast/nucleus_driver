#!/usr/bin/env python3
"""
Offline Pairing Collector Node for ROS 2 (Jazzy)

This node subscribes to the AHRS and WaterTrack topics,
collects all messages during a bag playback, and after playback,
performs offline pairing between water track messages and the closest-in-time AHRS messages.

For each pair, the node computes the sensor tilt using:
    tilt = arccos(cos(roll_rad) * cos(pitch_rad))
(with roll and pitch converted from degrees to radians),
and writes the paired data to a CSV file for later analysis/plotting.

Assumptions:
  - AHRS messages are published on '/nucleus_node/ahrs_packets' and contain fields:
      system_timestamp, roll, pitch, etc.
  - WaterTrack messages are published on '/nucleus_node/water_track_packets' and contain fields:
      system_timestamp, beam_1_velocity_valid, beam_2_velocity_valid, beam_3_velocity_valid,
      x_velocity_valid, y_velocity_valid, z_velocity_valid, etc.
  - Timestamps are extracted from system_timestamp (builtin_interfaces/Time).
  - Roll and pitch are assumed to be given in degrees.

To specify the output CSV filename (including path), use the command-line argument:
    --output-file <filename>
For example, in your Docker container with /data mapped:
    ./offline_pairing_collector.py --output-file /data/my_output.csv
"""

import rclpy
from rclpy.node import Node
import math
import csv
import argparse

# Import the message types. Adjust package names if necessary.
from interfaces.msg import AHRS, WaterTrack

def time_to_float(time_stamp):
    """
    Convert a builtin_interfaces/Time to a float (seconds).
    Assumes that the time_stamp has 'sec' and 'nanosec' attributes.
    """
    return float(time_stamp.sec) + float(time_stamp.nanosec) * 1e-9

def compute_tilt(roll_deg, pitch_deg):
    """
    Compute the sensor tilt relative to vertical given roll and pitch (in degrees).
    Uses the formula:
        tilt = arccos( cos(roll_rad) * cos(pitch_rad) )
    Returns the tilt in degrees.
    """
    roll_rad = math.radians(roll_deg)
    pitch_rad = math.radians(pitch_deg)
    cos_val = math.cos(roll_rad) * math.cos(pitch_rad)
    # Ensure the value is in the valid range [-1, 1] for arccos.
    cos_val = max(-1.0, min(1.0, cos_val))
    tilt_rad = math.acos(cos_val)
    return math.degrees(tilt_rad)

class OfflinePairingCollector(Node):
    def __init__(self):
        super(OfflinePairingCollector, self).__init__('offline_pairing_collector')
        self.get_logger().info("Offline Pairing Collector Node started.")

        # Lists to hold all received messages.
        self.ahrs_data = []      # Each element: {'time': float, 'roll': float, 'pitch': float}
        self.water_data = []     # Each element: {'time': float, 'water_quality': int}

        # Create subscriptions.
        self.create_subscription(
            AHRS,
            '/nucleus_node/ahrs_packets',
            self.ahrs_callback,
            10)
        self.create_subscription(
            WaterTrack,
            '/nucleus_node/water_track_packets',
            self.water_callback,
            10)

    def ahrs_callback(self, msg):
        """
        Callback for AHRS messages.
        Extracts the timestamp, roll, and pitch, and stores them in the ahrs_data list.
        """
        t = time_to_float(msg.system_timestamp)
        # Save roll and pitch (assumed to be in degrees)
        self.ahrs_data.append({'time': t, 'roll': msg.roll, 'pitch': msg.pitch})
        self.get_logger().debug("AHRS msg at {:.3f}: roll {:.2f}, pitch {:.2f}".format(t, msg.roll, msg.pitch))

    def water_callback(self, msg):
        """
        Callback for WaterTrack messages.
        Computes a water quality metric (a simple count of valid flags)
        and stores the message's timestamp and quality metric.
        """
        t = time_to_float(msg.system_timestamp)
        quality = 0
        # Count valid flags (you can adjust which flags you want to include)
        if msg.beam_1_velocity_valid:
            quality += 1
        if msg.beam_2_velocity_valid:
            quality += 1
        if msg.beam_3_velocity_valid:
            quality += 1
        if msg.x_velocity_valid:
            quality += 1
        if msg.y_velocity_valid:
            quality += 1
        if msg.z_velocity_valid:
            quality += 1

        self.water_data.append({'time': t, 'water_quality': quality})
        self.get_logger().debug("WaterTrack msg at {:.3f}: quality {}".format(t, quality))

    def offline_pairing(self):
        """
        Performs offline pairing between water track messages and the nearest-in-time AHRS messages.
        Returns a list of tuples: (AHRS_Time, Tilt_deg, WaterTrack_Time, WaterQuality)
        """
        pairs = []

        # Sort the messages by timestamp.
        self.ahrs_data.sort(key=lambda msg: msg['time'])
        self.water_data.sort(key=lambda msg: msg['time'])

        # For each water track message, find the closest AHRS message.
        for water_msg in self.water_data:
            water_time = water_msg['time']
            best_diff = float('inf')
            best_ahrs = None

            # Simple linear search; if performance becomes an issue, consider binary search.
            for ahrs_msg in self.ahrs_data:
                dt = abs(ahrs_msg['time'] - water_time)
                if dt < best_diff:
                    best_diff = dt
                    best_ahrs = ahrs_msg
                # Since ahrs_data is sorted, break early if dt starts increasing.
                elif ahrs_msg['time'] > water_time and dt > best_diff:
                    break

            if best_ahrs is not None:
                tilt_deg = compute_tilt(best_ahrs['roll'], best_ahrs['pitch'])
                pairs.append((best_ahrs['time'], tilt_deg, water_time, water_msg['water_quality']))

        return pairs

    def write_pairs_to_csv(self, pairs, filename):
        """
        Writes the paired data to a CSV file.
        CSV columns: AHRS_Time, Tilt_deg, WaterTrack_Time, WaterQuality.
        """
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['AHRS_Time', 'Tilt_deg', 'WaterTrack_Time', 'WaterQuality'])
                for pair in pairs:
                    writer.writerow(pair)
            self.get_logger().info("Wrote {} pairs to {}".format(len(pairs), filename))
        except Exception as e:
            self.get_logger().error("Error writing CSV: {}".format(e))


def main(args=None):
    # Parse command-line arguments.
    parser = argparse.ArgumentParser(
        description="Offline Pairing Collector for AHRS and WaterTrack topics")
    parser.add_argument(
        "--output-file",
        type=str,
        default="/data/paired_data_offline.csv",
        help="Full path and filename for the CSV output (e.g., /data/my_output.csv)")
    parsed_args, unknown = parser.parse_known_args()

    # Pass any remaining args to rclpy.
    rclpy.init(args=args)
    node = OfflinePairingCollector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt detected. Finishing offline pairing...")
    finally:
        # Perform offline pairing after bag playback or shutdown.
        pairs = node.offline_pairing()
        node.write_pairs_to_csv(pairs, filename=parsed_args.output_file)
        node.destroy_node()
        # Wrap shutdown in a try/except to ignore shutdown errors.
        try:
            if rclpy.ok():
                rclpy.shutdown()
        except Exception as e:
            # Log or ignore the error since shutdown is already called.
            pass

if __name__ == '__main__':
    main()
