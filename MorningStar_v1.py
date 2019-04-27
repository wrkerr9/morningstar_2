# Hello, and welcome to my Tristar Reading Code for the PC.
# This code has some bugs.
# Sometimes it reads everything just fine, sometimes it doesn't.
# It's completely random.
# I think it has something to do with the baudrate. It fluctuates a lot. I don't know what to do about it.



# From the Tristar MODBUS document:
# Parameters: 
# The TriStar MPPT supports RTU mode only.
# 16bit MODBUS addresses (per the modbus.org spec)
# The serial communication parameters:
#   - BPS 9600 baud
#   - Parity None
#   - Data bits 8
#   - Stop bits 1 or 2*
#   - Flow control None
#  *The TriStar accepts either 1 or 2 stop bits. It will send 2 stop bits to provide extra byte padding. The
#  connected PC can be set to receive either 1 or 2 stop bits.



# imports:

import pymodbus
import serial
import time
import sys
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse

from morningstar import *

# I will try experimenting with baudrates to see if it's possible to make it consistent.
# So far, 9600 baud is the only one that consistently connects at least one.
b_official = 9600
b_experimental = 9600

#to find a port, we will scan them all.
#every system uses different ports.
# The port number and format changes with the system. 
# Windows uses a virtual COM port system by saying "COM9".
# Linux uses a virtual COM port system by saying "/dev/ttyusb0".
# we must accommodate our code to this.

ports = []
if sys.platform.startswith('win'):
	ports = ['COM%s' % (i+1) for i in range(256)]
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
	import glob
	ports = glob.glob('/dev/ttyUSB*')
elif sys.platform.startswith('darwin'):
	import glob
	ports = glob.glob('/dev/tty.usbserial*')
else:
	raise EnvironmentError('Error finding ports on your operating system')
ports_used = []
for p in ports: 
	try:
		s = serial.Serial(port=p, baudrate=b_official)
		print(p)
		ports_used.append(p)
		s.close()
	except(OSError, serial.SerialException):
		pass
# To open a MODBUS client in python3, use ModbusSerialClient().
# We only use RTU mode.

print(ports_used)
connected = False
port = ""

for p in ports_used:
	try:
		client = ModbusSerialClient("rtu",port=p, baudrate=b_official,timeout=20)
		connected = client.connect()
		port = p
	except:
		pass
if not connected:
	print("Tristar not connected.")
	exit(1)
else:
	print("Connected on", port,"!")
	
# try:
	# data = retrieveScaling(client)
	# V_PU = 0
	# I_PU = 0
	# try:
		# V_PU_hi = data[0] #whole part of voltage scaling
		# V_PU_lo = data[1] #fractional part of voltage scaling
		# V_PU = V_PU_hi + (V_PU_lo >> 16) 
		# I_PU_hi = data[2] #whole part of voltage scaling 
		# I_PU_lo = data[3] #fractional part of voltage scaling 
		# I_PU = I_PU_hi + (I_PU_lo >> 16)
	# except:
		# print("Could not retrieve basic scaling information. Exiting.")
		# exit(1)
	# data = checkChargeSettings(client,V_PU, I_PU)
	# print(data)
# finally:
	# client.close()
	# exit(0)
try:
	
	data = retrieveScaling(client)
	V_PU = data[0] + data[1]*(2**-15)
	I_PU = data[2] + data[3]*(2**-15)
	#Reading Filtered ADC data
	#they're all signed. 
	#1.) battery voltage, filtered. scaling: n·V_PU·2-15
	#2.) battery terminal voltage, filtered
	#3.) battery sense voltage, filtered 
	#4.) Array voltage, filtered.
	data = retrieveADCVoltages(client, V_PU)
	try:
		bat_voltage = data[0]
		bat_terminal_voltage = data[1]
		bat_sense_voltage = data[2]
		array_voltage = data[3]
		
		print("Battery Voltage: ", bat_voltage)
		print("Battery Voltage at Terminal: ", bat_terminal_voltage)
		print("Battery Sense Voltage: ", bat_sense_voltage)
		print("Array Voltage: ", array_voltage)
	except:
		pass
	
	
	#Currents:
	#1.) Battery Current
	#2.) Array Current
	data = retrieveADCCurrents(client, I_PU)
	try:
		bat_current = data[0]
		array_current = data[1]
		print("Battery Current: ", bat_current)
		print("Array Current: ", array_current)
	except:
		pass
	#Temperatures:
	data = retrieveTemperatures(client)
	try:
		heatsink_temp = data[0]
		RTS_temp = data[1]
		bat_reg_temp = data[2]
		print("Heatsink temperature: " + str(heatsink_temp) + "C")
		print("RTS temperature: " + str(RTS_temp) + "C")
		print("Battery regulation temperature: " + str(bat_reg_temp) + "C")
	except:
		pass
	#read data: 
	#1.) absorption voltage at 25 degrees celsius
	#2. )float voltage at 25 degrees celsius 
	# ...
	# 12.) Battery Service Timer
	#read the modbus document.
	#it can't read 0xE003!
	chargeSettings = checkChargeSettings(client, V_PU, I_PU)
	try:
		print("Charge Settings: ", chargeSettings)
	except:
		pass
	#Today's values
	todaysValues = retrieveTodaysValues(client, V_PU, I_PU)
	try:
		print("Today's values: ", todaysValues)
	except:
		pass
	#Alarms
	alarms = retrieveAlarms(client)
	print("Alarms: ", alarms)
	
	#Faults
	faults = retrieveControllerFaults(client)
	try:
		print("Faults: ", faults)
	except:
		pass
	#LED State
	LEDState = retrieveLEDState(client)
	try:
		print("LEDState: ", LEDState)
	except:
		pass
	#DIP Switch
	DIPSwitch = retrieveDIPSwitch(client)
	try:
		print("DIP switch: ", DIPSwitch)
	except:
		pass
	
	#Charge State
	ChargeState = retrieveChargeState(client)
	try:
		print("Charge State: ", ChargeState)
	except: 
		pass
	
finally:
	print("Closing connection.")
	client.close()
