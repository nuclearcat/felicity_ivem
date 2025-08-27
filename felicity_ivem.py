#!/usr/bin/env python3
"""
This script reads data from a Modbus RTU inverter using the pymodbus library.
Compatible with Felicity IVEM5048(tested) and IVEM3024 (untested).
Potentially compatible with some Voltronic Axpert inverters.

Work modes and charging states are represented by the ``WorkMode`` and
``ChargingState`` enums defined in this file.
"""

from pymodbus.client.serial import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from enum import Enum
import logging
import time
import argparse
import paho.mqtt.client as mqtt

PORT_NAME = "/dev/ttyUSB0"  # Change this to your serial port

# Optional: enable logging for debugging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Enum representations of inverter states
class WorkMode(Enum):
    PowerOnMode = 0
    StandbyMode = 1
    BypassMode = 2
    BatteryMode = 3
    FaultMode = 4
    LineMode = 5
    PVChargeMode = 6


class ChargingState(Enum):
    NoCharge = 0
    ConstantCurrent = 1
    ConstantVoltage = 2
    Float = 3

# Modbus RTU client configuration
client = ModbusSerialClient(
    port=PORT_NAME, baudrate=2400, stopbits=1, bytesize=8, parity="N", timeout=4
)


class Inverter:
    register_map = {
        "model": 0xF801,
        "work_mode": 0x1101,
        "charging_state": 0x1102,
        "fault_code": 0x1103,
        "power_flow_msg": 0x1104,
        "battery_voltage": 0x1108,
        "battery_current": 0x1109,
        "battery_power": 0x110A,
        "ac_output_voltage": 0x1111,
        "ac_input_voltage": 0x1117,
        "ac_frequency": 0x1119,
        "ac_output_power": 0x111E,
        "ac_output_apparent_power": 0x111F,
        "load_percentage": 0x1120,
        "pv_input_voltage": 0x1126,
        "pv_input_power": 0x112A,
        "battery_percentage": 0x1132,
    }

    """
    WIP:

    output_source_priority: 0x212A ?????
    power priority: Utility First 
    1=PV priority Solar Frist 
    2=PV battery main power Solar Bat Utility

    application_mode: 0x212B
    0=APL
    1=UPS

    charging_source_priority: 0x212C
    1=PV priority Solar Frist
    2=PV and mains priority (SolarandUtility first)
    3=PV solar only

    Figure out battery voltages, how it is align with LiFePo4
    """

    wregister_map = {
        "ac_output_frequency": 0x2129,
        "output_source_priority": 0x212A,
        "application_mode": 0x212B,
        "charging_source_priority": 0x212C,
        "max_charging_current": 0x212E,
        "max_ac_charging_current": 0x212F,
        "buzzer_enabled": 0x2131,
        "overload_restart": 0x2133,
        "overtemperature_restart": 0x2134,
        "lcd_backlight": 0x2135,
        "overload_to_bypass": 0x2137,
    }

    def __init__(self, client):
        self.client = client
        self.last_values = {}

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read_holding_registers(self, address, count=1, slaveid=1):
        return self.client.read_holding_registers(
            address=address, count=count, slave=slaveid
        )

    def read_register_raw(self, address):
        """Retry on failure 3 times"""
        for i in range(3):
            try:
                result = self.client.read_holding_registers(address=address)
            except Exception as e:
                log.error(f"Error reading register {address}: {e}, retrying {i+1}/3")
                time.sleep(1)
                continue
            if not result.isError():
                return result
            else:
                log.error(
                    f"Error reading register {address}: {result}, retrying {i+1}/3"
                )
        return None

    def write_register(self, address, value):
        """Write a 2-byte value to a register"""
        result = self.client.write_register(address, value)
        if not result.isError():
            return True
        else:
            log.error(f"Error writing register {address}: {result}")
            return False

    def read_register(self, name):
        # print(f"Reading register: {name}")
        convert_types = {
            "battery_power": self.client.DATATYPE.INT16,
            "battery_current": self.client.DATATYPE.INT16,
            "ac_output_power": self.client.DATATYPE.INT16,
            "ac_output_apparent_power": self.client.DATATYPE.INT16,
        }
        if name in self.register_map:
            address = self.register_map[name]
            count = 1
            if name in convert_types:
                data_type = convert_types[name]
            else:
                data_type = self.client.DATATYPE.UINT16
            # Read the register
            result = self.read_register_raw(address)
            if not result.isError():
                val = self.client.convert_from_registers(result.registers, data_type)
                # normalize the value
                nval = self.normalize_register(name, val)
                if nval is not None:
                    # Store the last value
                    self.last_values[name] = nval
                    return nval
                else:
                    log.error(f"Error normalizing register {name}")
                    return None
            else:
                log.error(f"Error reading register {name}: {result}")
                return None

    # List registers and associate with normalized names
    def get_register_by_name(self, name):
        return self.register_map.get(name)

    # normalize register values to unified format, e.g. register volts^2 to float
    def normalize_register(self, register, value):
        if register in self.register_map:
            if register == "battery_voltage":
                value = value * 0.01
                value = round(value, 2)
                return value
            elif register == "ac_input_voltage":
                value = value * 0.1
                value = round(value, 2)
                return value
            elif register == "ac_output_voltage":
                value = value * 0.1
                value = round(value, 2)
                return value
            elif register == "ac_frequency":
                value = value * 0.01
                value = round(value, 2)
                return value
            elif register == "pv_input_voltage":
                value = value * 0.1
                value = round(value, 2)
                return value
            elif register == "work_mode":
                try:
                    return WorkMode(value).name
                except ValueError:
                    return "Unknown"
            elif register == "charging_state":
                try:
                    return ChargingState(value).name
                except ValueError:
                    return "Unknown"
            elif register == "model":
                models = {
                    0x0408: "IVEM5048(5000VA/48V)",
                    0x0204: "IVEM3024(3000VA/24V)",
                }
                return models.get(value, "Unknown")
            else:
                return value
        else:
            log.error(f"Register {register} not found in register map.")
            return None

    def read_all_registers(self):
        all_registers = {}
        for name in self.register_map:
            value = self.read_register(name)
            if value is not None:
                all_registers[name] = value
            else:
                log.error(f"Failed to read register {name}")
        return all_registers

    def human_time(self, seconds):
        """Convert seconds to human-readable format HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def estimate_battery_runtime(self):
        """Estimate battery runtime based on battery percentage and average load(power in W)
        Read until percentage flips to lower level, record timestamp, start recording power values each 10 seconds
        when next percentage is lower than previous, calculate average power vs time elapsed
        """
        current_percentage = self.read_register("battery_percentage")
        if current_percentage is None:
            log.error("Failed to read battery percentage")
            return None
        # Read until percentage flips to lower level
        print("Waiting for battery percentage to drop...")
        while True:
            new_percentage = self.read_register("battery_percentage")
            if new_percentage is None:
                log.error("Failed to read battery percentage")
                return None
            if new_percentage < current_percentage:
                current_percentage = new_percentage
                break
            current_percentage = new_percentage
        # Record timestamp
        print("Starting battery runtime estimation... ")
        print(f"Current battery percentage: {current_percentage}%")
        start_time = time.time()

        # Record power values each 10 seconds
        power_values = []
        while True:
            power = self.read_register("battery_power")
            if power is None:
                log.error("Failed to read battery power")
                return None
            power_values.append(power)
            print(".", end="")
            new_percentage = self.read_register("battery_percentage")
            if new_percentage is None:
                log.error("Failed to read battery percentage")
                return None
            if new_percentage < current_percentage:
                break
            time.sleep(5)

        print("\nBattery percentage dropped to:", new_percentage)
        # Calculate average power
        average_power = sum(power_values) / len(power_values)
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        print(
            f"Average power: {average_power} W consumes 1% of battery in {self.human_time(elapsed_time)}"
        )
        # Calculate estimated runtime (to 20% of battery)
        estimated_runtime = (current_percentage - 20) * elapsed_time
        print(f"Estimated runtime: {self.human_time(estimated_runtime)}")
        # Calculate battery pack capacity in Kwh
        battery_capacity = (average_power * -1) * 100 / (3600 / elapsed_time) / 1000
        print(f"Battery capacity: {battery_capacity} KWh")

        return estimated_runtime

def reconnect_loop(mclient):
    """Reconnect to MQTT server"""
    while True:
        try:
            mclient.reconnect()
        except Exception as e:
            log.error(f"Failed to reconnect: {e}")
            time.sleep(10)
        break

def mqtt_publoop(args, inverter):
    """Publish data to MQTT server"""
    mclient = mqtt.Client()
    mclient.connect(args.mqttserver, 1883, 60)
    while True:
        all_registers = inverter.read_all_registers()
        if all_registers is not None:
            for name, value in all_registers.items():
                log.info(f"{name}: {value}")
                mclient.publish(f"{args.mqttprefix}/{name}", value)
        else:
            log.error("Failed to read all registers")
        rc = mclient.loop(timeout=1)
        if rc != 0:
            log.error(f"MQTT error: {rc}")
            reconnect_loop(mclient)
        time.sleep(10)


def main():
    parser = argparse.ArgumentParser(
        description="Read data from Felicity IVEM inverter"
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Estimate battery runtime and capacity",
    )
    parser.add_argument(
        "--printall",
        action="store_true",
        help="Print all registers",
    )
    parser.add_argument(
        "--scanunknown",
        action="store_true",
        help="Scan unknown registers from 0x1100 to 0x112F",
    )
    parser.add_argument(
        "--mqttserver",
        help="Enable MQTT publishing",
    )
    parser.add_argument(
        "--mqttprefix",
        default="felicity",
        help="MQTT topic prefix (default: felicity)",
    )
    args = parser.parse_args()
    inverter = Inverter(client)
    if inverter.connect():
        log.info("Connected to inverter")
        if args.estimate:
            estimate_battery_runtime = inverter.estimate_battery_runtime()
            if estimate_battery_runtime is not None:
                log.info(f"Estimated battery runtime: {estimate_battery_runtime}")
            else:
                log.error("Failed to estimate battery runtime")
        if args.printall:
            all_registers = inverter.read_all_registers()
            for name, value in all_registers.items():
                log.info(f"{name}: {value}")
        if args.scanunknown:
            log.info("Scanning unknown registers from 0x1100 to 0x112F")
            try:
                # scan from 0x1100 to 0x112F
                for i in range(0x1100, 0x112F + 1):
                    result = inverter.read_holding_registers(i, 1)
                    if not result.isError():
                        val = inverter.client.convert_from_registers(
                            result.registers, inverter.client.DATATYPE.UINT16
                        )
                        log.info(f"Register {hex(i)}: {val} {hex(val)}")
                    else:
                        log.error(f"Error reading register {i}: {result}")
            except Exception as e:
                log.error(f"Error reading registers: {e}")
        if args.mqttserver:
            # fork to run in background TODO
            log.info("Starting MQTT client")
            log.info(f"Connecting to MQTT server {args.mqttserver}")
            mqtt_publoop(args, inverter)
        inverter.close()
    else:
        log.error("Failed to connect to inverter")


if __name__ == "__main__":
    main()
