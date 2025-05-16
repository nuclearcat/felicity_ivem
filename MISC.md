Register Map:
0xF801 - 0x0408 - 5048 (5000VA/48V) 0x0204 - 3024 (3000VA/24V)
0x1101 - Working mode
0=power-on mode/PowerOnMode
1=standby mode/StandbyMode
2=bypass mode/Bypass Mode
3=battery mode/BatteryMode
4=fault mode/FaultMode
5=mains mode/LineMode
6=chargingmode/PVChargeMode
0x1102 - Battery charging state
0=no charging / No charge
1=Constant current
2=Constant voltage charge/Absorption charge
3=Float charge/Float charge
0x1103 - Fault code
0x1104 - Power flow message
0x1108 - Battery Voltage
0x1109 - Battery Current
0x110A - Battery Power
0x1107 - AC input voltage
0x1119 - AC Frequency
0x111E - AC output active power
0x111F - AC output apparent power

Decoding(normalizing) the registers:
# PowerFlowMsg
# b15: 0: Battery disconnected, 1: Battery connected
# b14: 0: Line abnormal, 1: Line normal
# b13: 0: PV input abnormal, 1: PV input normal
# b12: 0: Load connect unallowed, 1: Load connect allowed
# b11b10: 00: No power flow, 01: Battery charging, 10: Battery discharging
# b9b8: 00: No power flow, 01: Draw power from line, 10: Feed power to line
# b7: 0: No power flow 1: PV MPPT working
# b6: 0: No power flow 1: LOad connected
# b0: 0: Power flow version unsupported, 1: Power flow version supported

# WorkingMode
    0: "PowerOnMode",
    1: "StandbyMode",
    2: "BypassMode",
    3: "BatteryMode",
    4: "FaultMode",
    5: "LineMode",
    6: "PVChargeMode"

These values are available programmatically as the `WorkMode` and
`ChargingState` enums in `felicity_ivem.py`.

# model
# 0xF801 - 0x0408 - 5048 (5000VA/48V) 0x0204 - 3024 (3000VA/24V)
