# Felicity IVEM python Client

## Overview

Felicity IVEM is a Python client for the Felicity IVEM 5048/3024 inverter. It allows you to monitor and control the inverter using a serial connection (RS232). The client provides a simple interface to read and write registers, as well as decode the data received from the inverter.

## Features

- Read and write registers
- Decode data received from the inverter
- Monitor inverter status
- MQTT support, compatible with Home Assistant
- Control inverter settings (TODO)

## Installation

Install the required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

## Example data

```
INFO:root:model: IVEM5048(5000VA/48V)
INFO:root:work_mode: BatteryMode
INFO:root:charging_state: ConstantCurrent
INFO:root:fault_code: 0
INFO:root:power_flow_msg: 47297
INFO:root:battery_voltage: 52.43
INFO:root:battery_current: -2
INFO:root:battery_power: -146
INFO:root:ac_input_voltage: 0.0
INFO:root:ac_frequency: 0.0
INFO:root:ac_output_power: 255
INFO:root:ac_output_apparent_power: 317
INFO:root:load_percentage: 7
INFO:root:pv_input_voltage: 340.0
INFO:root:pv_input_power: 231
INFO:root:battery_percentage: 50
```