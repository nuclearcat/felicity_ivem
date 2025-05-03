#!/usr/bin/env python3
"""
This script reads data from a Modbus RTU inverter using the pymodbus library.
Compatible with Felicity IVEM5048(tested) and IVEM3024 (untested).
Potentially compatible with some Voltronic Axpert inverters.
"""

from pymodbus.client.serial import ModbusSerialClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
import logging

PORT_NAME = "/dev/ttyUSB0"  # Change this to your serial port

# Optional: enable logging for debugging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# Modbus RTU client configuration
client = ModbusSerialClient(
    port=PORT_NAME,
    baudrate=2400,
    stopbits=1,
    bytesize=8,
    parity='N',
    timeout=4
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
        "ac_input_voltage": 0x1107,
        "ac_frequency": 0x1119,
        "ac_output_power": 0x111E,
        "ac_output_apparent_power": 0x111F,
        "load_percentage": 0x1120,
        "pv_input_voltage": 0x1126,
        "pv_input_power": 0x112A,
        "battery_percentage": 0x1132
    }

    def __init__(self, client):
        self.client = client

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def read_holding_registers(self, address, count=1, slaveid=1):
        return self.client.read_holding_registers(address=address, count=count, slave=slaveid)

    def read_register(self, name):
        #print(f"Reading register: {name}")
        convert_types = {
            "battery_power": self.client.DATATYPE.INT16,
            "battery_current": self.client.DATATYPE.INT16,
            "ac_output_power": self.client.DATATYPE.INT16,
            "ac_output_apparent_power": self.client.DATATYPE.INT16
        }
        if name in self.register_map:
            address = self.register_map[name]
            count = 1
            if name in convert_types:
                data_type = convert_types[name]
            else:
                data_type = self.client.DATATYPE.UINT16
            result = self.read_holding_registers(address, count)
            if not result.isError():
                val = self.client.convert_from_registers(result.registers, data_type)
                # normalize the value
                nval = self.normalize_register(name, val)
                if nval is not None:
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
                return value * 0.01
            elif register == "ac_input_voltage":
                return value * 0.1
            elif register == "ac_frequency":
                return value * 0.01
            elif register == "work_mode":
                modes = {
                    0: "PowerOnMode",
                    1: "StandbyMode",
                    2: "BypassMode",
                    3: "BatteryMode",
                    4: "FaultMode",
                    5: "LineMode",
                    6: "PVChargeMode"
                }
                return modes.get(value, "Unknown")
            elif register == "charging_state":
                states = {
                    0: "NoCharge",
                    1: "ConstantCurrent",
                    2: "ConstantVoltage",
                    3: "Float"
                }
                return states.get(value, "Unknown")
            elif register == "model":
                models = {
                    0x0408: "IVEM5048-(5000VA/48V)",
                    0x0204: "IVEM3024-(3000VA/24V)"
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

def main():
    inverter = Inverter(client)
    if inverter.connect():
        log.info("Connected to inverter")
        try:
            # Read all registers
            all_registers = inverter.read_all_registers()
            for name, value in all_registers.items():
                log.info(f"{name}: {value}")
        except Exception as e:
            log.error(f"Error reading registers: {e}")
        finally:
            inverter.close()
    else:
        log.error("Failed to connect to inverter")
        
if __name__ == "__main__":
    main()
