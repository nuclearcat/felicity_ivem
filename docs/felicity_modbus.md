# Felicity High‑Frequency Inverter(IVEM) – External Communication Protocol

*Document date in source: 2021‑06‑08*

---

## 1. Communication Interface

* **Physical layer:** UART
* **Baud rate:** 2400 bps
* **Data bits:** 8
* **Stop bits:** 1
* **Parity:** none
* **Flow control:** none
* **Duplex:** half‑duplex. At any moment, only one side transmits while the other receives.
* **Protocol:** MODBUS RTU. The external controller (host) always initiates communication; the inverter responds (the inverter never initiates frames).

---

## 2. Frame Definition (Structure)

| Field             | Length  | Notes                                            |
| ----------------- | ------- | ------------------------------------------------ |
| **Slave address** | 1 byte  | `1…31` (decimal). `31` is the broadcast address. |
| **Function code** | 1 byte  | See supported function codes below.              |
| **Data field**    | N bytes | Contains address fields and payload.             |
| **CRC**           | 2 bytes | 16‑bit CRC.                                      |

### Supported function codes

* `0x03` – Read multiple holding registers
* `0x06` – Write single holding register
* `0x10` – Write multiple holding registers
* `0x17` – Master‑slave synchronous data
* `0x41` – Firmware upgrade

### 2.1 Commands & frame notes

* **CRC coverage:** from *Slave address* through the end of the *Data field* (CRC bytes themselves are **not** included).

#### 2.1.1 `0x03` – Read multiple registers

Reads a contiguous block of holding registers. The request specifies the starting register address and the number of registers. In the response, each register is returned as **two bytes** (big‑endian: high byte first, then low byte).

**Example:** Read registers `0x0001–0x0002`.

**Request (byte order):**

| Byte(s) | Meaning                        |
| ------- | ------------------------------ |
| 1       | Slave address                  |
| 2       | Function (`0x03`)              |
| 3–4     | Starting address (Hi, Lo)      |
| 5–6     | Quantity of registers (Hi, Lo) |
| 7–8     | CRC (Lo, Hi)                   |

**Response (byte order):**

| Byte(s) | Meaning                                     |
| ------- | ------------------------------------------- |
| 1       | Slave address                               |
| 2       | Function (`0x03`)                           |
| 3       | Byte count = 2 × quantity                   |
| 4–…     | Register values (for each register: Hi, Lo) |
| last 2  | CRC (Lo, Hi)                                |

#### 2.1.2 `0x06` – Write single register

Writes one holding register on the slave. The normal response echoes the request (address, function, register address, and the value written).

**Example:** Write `0xAAAA` to register address `0x0008`.

**Request / Response (byte order):**

| Byte(s) | Meaning                   |
| ------- | ------------------------- |
| 1       | Slave address             |
| 2       | Function (`0x06`)         |
| 3–4     | Register address (Hi, Lo) |
| 5–6     | Value (Hi, Lo)            |
| 7–8     | CRC (Lo, Hi)              |

#### 2.1.3 `0x10` – Write multiple registers

Writes a contiguous block of registers. The request carries a byte count followed by the sequence of register values.

**Example:** Write `0x1194` to `0x0001` and `0x01CC` to `0x0002`.

**Request (byte order):**

| Byte(s) | Meaning                                     |
| ------- | ------------------------------------------- |
| 1       | Slave address                               |
| 2       | Function (`0x10`)                           |
| 3–4     | Starting register address (Hi, Lo)          |
| 5–6     | Quantity of registers to write (Hi, Lo)     |
| 7       | Byte count = 2 × quantity                   |
| 8–…     | Register values (for each register: Hi, Lo) |
| last 2  | CRC (Lo, Hi)                                |

**Normal response (byte order):**

| Byte(s) | Meaning                                |
| ------- | -------------------------------------- |
| 1       | Slave address                          |
| 2       | Function (`0x10`)                      |
| 3–4     | Starting register address (Hi, Lo)     |
| 5–6     | Quantity of registers written (Hi, Lo) |
| 7–8     | CRC (Lo, Hi)                           |

---

## 3. Data Register Map

> **Types**
>
> * `INT16U`: unsigned 16‑bit integer
> * `INT16S`: signed 16‑bit integer
> * **Scale** column: a value of `-1` means divide by 10; `-2` means divide by 100; `0` means no scaling. Units shown after scaling.
> * **Attr**: `R`=Read‑only, `R/W`=Readable & writable.

### 3.1 Information Data

| Address (Hex) | Size (words) | Name             | Type   | Scale | Unit | Attr | Description            | Notes                                                                                                                                                             |
| ------------- | ------------ | ---------------- | ------ | ----- | ---- | ---- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0xF800`      | 1            | Type             | INT16U | 0     | –    | R    | Device type (category) | `0x50` = High‑frequency inverter                                                                                                                                  |
| `0xF801`      | 1            | SubType          | INT16U | 0     | –    | R    | Device subtype         | `0x0204`: 3024 (3000 VA / 24 V); `0x0408`: 5048 (5000 VA / 48 V)                                                                                                  |
| `0xF804`      | 5            | Serial number    | INT16U | 0     | –    | R    | Serial number (SN)     | Model can also be derived from SN. SN is 14 digits, e.g., `01354820250001` → SN\[0]=0135; SN\[1]=4820; SN\[2]=2500; SN\[3]=0100; SN\[4]=0000. Invalid = `0x0000`. |
| `0xF80B`      | 1            | CPU1 F/W Version | INT16U | −2    | –    | R    | CPU1 firmware version  | Invalid = `0xFFFF`                                                                                                                                                |
| `0xF80C`      | 1            | CPU2 F/W Version | INT16U | −2    | –    | R    | CPU2 firmware version  | Invalid = `0xFFFF`                                                                                                                                                |

### 3.2 Realtime Data

| Address (Hex) | Size (words) | Name                     | Type   | Scale | Unit | Attr | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ------------- | ------------ | ------------------------ | ------ | ----- | ---- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `0x1100`      | 1            | SettingDataSn            | INT16U | 0     | –    | R    | Settings area serial number; increments by 1 when any setting changes.                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `0x1101`      | 1            | Working mode             | INT16U | 0     | –    | R    | Mode: `0` Power‑On; `1` Standby; `2` Bypass; `3` Battery; `4` Fault; `5` Line; `6` PV Charge.                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `0x1102`      | 1            | Battery charging stage   | INT16U | 0     | –    | R    | State: `0` No charge; `1` Bulk (CC); `2` Absorption (CV); `3` Float.                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `0x1103`      | 1            | Fault Code               | INT16U | 0     | –    | R    | Fault ID (see separate fault/alarm table).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `0x1104`      | 1            | PowerFlowMsg             | INT16U | 0     | –    | R    | Power‑flow status bit‑field:**b15** 0: Battery disconnected, 1: Battery connected**b14** 0: Line abnormal, 1: Line normal**b13** 0: PV input abnormal, 1: PV input normal**b12** 0: Load connection not allowed, 1: Load connection allowed**b11..b10** `00` No power flow, `01` Battery charging, `10` Battery discharging**b9..b8** `00` No power flow, `01` Draw from Line, `10` Feed to Line**b7** 0: No power flow, 1: PV MPPT working**b6** 0: No power flow, 1: Load connected**b0** 0: Power‑flow version unsupported, 1: Supported. |
| `0x1108`      | 1            | Battery voltage          | INT16U | −2    | V    | R    | Battery voltage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `0x1109`      | 1            | Battery current          | INT16S | 0     | A    | R    | Battery current (signed; negative = discharge)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `0x110A`      | 1            | Battery power            | INT16S | 0     | W    | R    | Battery power (signed; negative = discharge)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `0x1111`      | 1            | AC output voltage        | INT16U | −1    | V    | R    | AC output voltage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `0x1117`      | 1            | AC input voltage         | INT16U | −1    | V    | R    | AC input voltage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `0x1119`      | 1            | AC input frequency       | INT16U | −2    | Hz   | R    | AC input frequency                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `0x111E`      | 1            | AC output active power   | INT16S | 0     | W    | R    | Output active power                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `0x111F`      | 1            | AC output apparent power | INT16U | 0     | VA   | R    | Output apparent power                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `0x1120`      | 1            | Load percentage          | INT16U | 0     | %    | R    | Load percentage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `0x1126`      | 1            | PV input voltage         | INT16U | −1    | V    | R    | PV voltage                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `0x112A`      | 1            | PV input power           | INT16S | 0     | W    | R    | PV power                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

### 3.3 Setting Data

> **Model note:** For voltage settings using `pcs` in the *Range* column, use `pcs=2` for model **3024** and `pcs=4` for model **5048**. Where shown as `value/pcs`, multiply by `pcs`, then apply the scale.

| Address (Hex) | Size (words) | Name                              | Type   | Scale | Unit | Attr | Description                         | Default | Min       | Max           | Range / Notes                                                                                                                               |
| ------------- | ------------ | --------------------------------- | ------ | ----- | ---- | ---- | ----------------------------------- | ------- | --------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `0x211F`      | 1            | Battery cut‑off voltage           | INT16U | −1    | V    | R/W  | Discharge cut‑off voltage           | 420     | `105/pcs` | `135/pcs`     | 3024: 21.0–27.0 V; 5048: 42.0–54.0 V                                                                                                        |
| `0x2122`      | 1            | Battery C.V charging voltage      | INT16U | −1    | V    | R/W  | Absorption voltage                  | 576     | `120/pcs` | `150/pcs`     | 3024: 24.0–30.0 V; 5048: 48.0–60.0 V                                                                                                        |
| `0x2123`      | 1            | Battery floating charging voltage | INT16S | −1    | V    | R/W  | Float voltage                       | 544     | `120/pcs` | `150/pcs`     | 3024: 24.0–30.0 V; 5048: 48.0–60.0 V                                                                                                        |
| `0x2129`      | 1            | AC output frequency               | INT8U  | 0     | –    | R/W  | Frequency select                    | `0`     | `0`       | `1`           | `0` = 50 Hz, `1` = 60 Hz                                                                                                                    |
| `0x212A`      | 1            | Output source priority            | INT8U  | 0     | –    | R/W  | Output priority                     | `0`     | `0`       | `2`           | `0` Utility First; `1` Solar First; `2` Solar‑Battery‑Utility                                                                               |
| `0x212B`      | 1            | Application Mode                  | INT8U  | 0     | –    | R/W  | Application mode                    | `0x00`  | `0`       | `1`           | `0` = APL; `1` = UPS                                                                                                                        |
| `0x212C`      | 1            | Charging source priority          | INT8U  | 0     | –    | R/W  | Charge priority                     | `1`     | `1`       | `3`           | `1` Solar First; `2` Solar & Utility First; `3` Solar Only                                                                                  |
| `0x212D`      | 1            | Battery type                      | INT8U  | 0     | –    | R/W  | Battery chemistry                   | `0`     | `0`       | `3`           | `0` AGM (gel); `1` Flooded; `2` User‑defined; `3` LiFePO₄                                                                                   |
| `0x212E`      | 1            | Max. charging current             | INT8U  | 0     | A    | R/W  | Total charge current (1 A steps)    | 60      | 10        | 100           | 10–100 A                                                                                                                                    |
| `0x2130`      | 1            | Max. AC charging current          | INT8U  | 0     | A    | R/W  | AC charge current (1 A steps)       | 30      | 10        | 100           | 10–100 A                                                                                                                                    |
| `0x2131`      | 1            | Buzzer enable                     | INT8U  | 0     | –    | R/W  | Buzzer                              | `0x01`  | 0         | 1             | `0` disable; `1` enable                                                                                                                     |
| `0x2133`      | 1            | Overload restart enable           | INT8U  | 0     | –    | R/W  | Overload auto‑restart               | `0x00`  | 0         | 1             | `0` disable; `1` enable                                                                                                                     |
| `0x2134`      | 1            | Over‑temperature restart enable   | INT8U  | 0     | –    | R/W  | Over‑temperature auto‑restart       | `0x00`  | 0         | 1             | `0` disable; `1` enable                                                                                                                     |
| `0x2135`      | 1            | LCD backlight enable              | INT8U  | 0     | –    | R/W  | Backlight                           | `0x01`  | 0         | 1             | `0` disable; `1` enable                                                                                                                     |
| `0x2137`      | 1            | Overload to bypass                | INT8U  | 0     | –    | R/W  | Switch to bypass on overload        | `0x00`  | 0         | 1             | `0` disable; `1` enable                                                                                                                     |
| `0x2156`      | 1            | Battery back‑to‑charge voltage    | INT16U | −1    | V    | R/W  | Battery low‑to‑charge threshold     | 460     | `110/pcs` | `135/pcs`     | 3024: 22.0–27.0 V; 5048: 44.0–54.0 V                                                                                                        |
| `0x2159`      | 1            | Battery back‑to‑discharge voltage | INT16U | −1    | V    | R/W  | Battery high‑to‑discharge threshold | 540     | `120/pcs` | `150/pcs` + 1 | 3024: 24.0–30.1 V (`30.1` = FULL); 5048: 48.0–60.1 V (`60.1` = FULL). If exceeded, **FULL** is shown. For model 5048, `601` indicates FULL. |

---

**End of document**
