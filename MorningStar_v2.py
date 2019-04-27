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

import serial

import modbus_tk
import sys
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

from morningstar_lib import *

# I will try experimenting with baudrates to see if it's possible to make it consistent.
# So far, 9600 baud is the only one that consistently connects at least one.
b_official = 9600

#to find a port, we will scan them all.
#every system uses different ports.
# The port number and format changes with the system. 
# Windows uses a virtual COM port system by saying "COM9".
# Linux uses a virtual COM port system by saying "/dev/ttyusb0".
# we must accommodate our code to this.
#
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
#PORTS_USED is an array of ports that I can use.
ports_used = []
for p in ports: 
	try:
		s = serial.Serial(port=p, baudrate=b_official)
		ports_used.append(p)
		s.close()
	except(OSError, serial.SerialException):
		pass
	
	
	
	
# To open a MODBUS client in python3 with modbus_tk, use modbus_rtu.RtuMaster.
# I'm importing it as ModbusSerialClient.
# We only use RTU mode.

connected = False
master = ""
port = ""
#I would like a logger to be used.
logger = modbus_tk.utils.create_logger("console")
#try:

	# PORT_ACTUAL = "COM4"
	# master = modbus_rtu.RtuMaster(
			# serial.Serial(port=PORT_ACTUAL, baudrate=b_official,bytesize=8,parity='N',
			# stopbits=1,xonxoff=0)
	# )
	# master.set_timeout(5.0)
	# master.set_verbose(True)
	# logger.info("connected")
	# logger.info(master.execute(1,cst.READ_HOLDING_REGISTERS,0,4))
	# x = master.execute(1,cst.READ_HOLDING_REGISTERS,0,4)
	# print(x)
# except modbus_tk.modbus.ModbusError as exc:
	# logger.error("%s- Code=%d",exc, exc.get_exception_code())
	# exit(1)
for p in ports_used:
	try:
		master = modbus_rtu.RtuMaster(
			serial.Serial(port=p, baudrate=b_official,bytesize=8,parity='N',
			stopbits=1,xonxoff=0)
		)
		connected = True
		port = p
	except:
		pass

if not connected:
	print("Tristar not connected.")
	exit(1)
else:
	print("Connected on", port,"!")

try:
	
	data = master.execute(1,cst.READ_HOLDING_REGISTERS,0,4)
	print(data)
	V_PU = data[0] + data[1]*(2**-15)
	I_PU = data[1] + data[2]*(2**-15)
	#Reading Filtered ADC data
	#they're all signed. 
	#1.) battery voltage, filtered. scaling: n·V_PU·2-15
	#2.) battery terminal voltage, filtered
	#3.) battery sense voltage, filtered 
	#4.) Array voltage, filtered.
	data = retrieveADCVoltages(master, V_PU)
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
	data = retrieveADCCurrents(master, I_PU)
	try:
		bat_current = data[0]
		array_current = data[1]
		print("Battery Current: ", bat_current)
		print("Array Current: ", array_current)
	except:
		print("FUCK YOU")
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
	chargeSettings = checkChargeSettings(master, V_PU, I_PU)
	try:
		print("Charge Settings: ", chargeSettings)
	except:
		pass
	#Today's values
	todaysValues = retrieveTodaysValues(master, V_PU, I_PU)
	try:
		print("Today's values: ", todaysValues)
	except:
		pass
	#Alarms
	alarms = retrieveAlarms(master)
	print("Alarms: ", alarms)
	
	#Faults
	faults = retrieveControllerFaults(master)
	try:
		print("Faults: ", faults)
	except:
		pass
	#LED State
	LEDState = retrieveLEDState(master)
	try:
		print("LEDState: ", LEDState)
	except:
		pass
	#DIP Switch
	DIPSwitch = retrieveDIPSwitch(master)
	try:
		print("DIP switch: ", DIPSwitch)
	except:
		pass
	
	#Charge State
	ChargeState = retrieveChargeState(master)
	try:
		print("Charge State: ", ChargeState)
	except: 
		pass
	
finally:
	print("Closing connection.")
	master._do_close()
