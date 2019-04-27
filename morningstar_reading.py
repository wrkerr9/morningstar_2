#!/usr/bin/env python
"""
Pymodbus Asynchronous Client Examples
--------------------------------------------------------------------------
The following is an example of how to use the asynchronous modbus
client implementation from pymodbus with ayncio.
The example is only valid on Python3.4 and above
"""
"""
The Raspberry Pi would be the master,
the Tristar MPPT would be the slave.
in MODBUS, two tables store
on/off discrete values (coils),
and two store numerical values (registers).
MODBUS uses a slave ID system. Each Tristar has its own slave ID.
Are we using MODBUS ASCII or MODBUS RTU?
ASCII => Transmitted in ASCII characters. Has a start of text indication. is ssafer.
RTU => Transmitted in binary Does not have a start of text indication. Is faster.
"""

"""
For Tristar MPPT:

Supports RTU mode only.

16-bit MODBUS addresses.

Serial Communication Parameters:
BPS: 9600 baud
Parity: None
Data bits: 8
Stop bits: 1 or 2*
Flow Control: None
*The TriStar accepts either 1 or 2 stop bits. It will send 2 stop bits to provide extra byte padding. 
The connected PC can be set to receive either 1 or 2 stop bits.

Default TCP communication parameters:

DHCP enabled
Port 502
MODBUS ID: 1
NETBIOS address: tsmppt + serial number (no spaces)
LiveView webaddress: http://tsmpptXXXXXXX (where X is the Serial Number)

"""
import time
import pymodbus3
import serial
import traceback
from pymodbus3.pdu import ModbusRequest
from pymodbus3.client.sync import ModbusSerialClient as ModbusClient
from pymodbus3.transaction import ModbusRtuFramer
from serial.tools.list_ports import comports
import sys

READ_COILS_PDU_Addr_Test_1 = 0x1000
SLAVE_UNIT = 0x1

client = ModbusClient("rtu", port="COM9", stopbits=2, bytesize=8, baudrate=9600,timeout=10)
connected = client.connect()
if connected:
	print("Tristar Morningstar 1 connected!")
else:
	print("Something went wrong.")
	exit(1)
start = time.time()
rr = client.read_holding_registers(0xE000, 1, unit=0)
assert(rr.function_code < 0x80)
print(rr)
#data = client.read_coils(READ_COILS_PDU_Addr_Test_1, 1)






stop = time.time()
if data:
	succ = "was successful"
else:
	succ = "failed"
print("read %s, time spent reading: %fs" % (succ, stop - start))
print("Data read:")
print(data)
client.close()
try:
	data = client.read_coils(READ_COILS_PDU_Addr_Test_1, 1)
	stop = time.time()
	if data:
		succ = "was successful"
	else:
		succ = "failed"
	print("read %s, time spent reading: %fs" % (succ, stop - start))
	print("Data read:")
	print(data)
	client.close()
except pymodbus3.exceptions.ModbusIOException:
	print("SHIT!!!")
	print(pymodbus3.exceptions.ModbusIOException.__cause__)
	print(pymodbus3.exceptions.ModbusIOException.__context__)
except:
	print("Something went wrong.")
finally:
	client.close()
	exit(1)