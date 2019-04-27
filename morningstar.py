#This is a library to retrieve data from the Tristar Morningstar MPPT device.

# Methods to retrieve data:
import pymodbus
from pymodbus.client.sync import ModbusSerialClient
from pymodbus.register_read_message import ReadHoldingRegistersResponse
def checkHoldingRegisters(client, address, count, tries=1):
	flag = 0
	while(flag < tries):
		data = client.read_input_registers(address,count, unit=1)
		if not data.isError():
			if hasattr(data, 'function_code'):
				assert(data.function_code < 0x80)
			if hasattr(data, 'registers'):
				print("Attempts:", flag)
				return data.registers
		else:
			client.close()
			client.connect()
		flag +=1
	print("Could not find data after", flag, "tries.")
def checkForRegisters(client, address, count, tries=1):
	"""
	# Method checkForRegisters(): reads the addresses for you. Will try multiple times.
	# this method exists because of the unreliability of my machine.
	#
	# @argument: client: what client are you polling?
	# @argument: address: what address of register are you reading?
	# @argument: count: how many spaces are you reading?
	# @argument: tries: how many times will you try to read it?
	#
	# @return: 
	# the register array.
	# returns blank array if data not found.
	"""
	flag = 0
	while(flag < tries):
		data = client.read_holding_registers(address, count, unit=1)
		if not data.isError():
			if hasattr(data, 'function_code'):
				assert(data.function_code < 0x80)
			if hasattr(data, 'registers'):
				print("Attempts:", flag)
				return data.registers
		else:
			client.close()
			client.connect()
			flag += 1
	print("Could not find data after", flag , "tries.")
	return []
	


def retrieveScaling(client):
	"""
	retrieveScaling(): Retreives the scaling terms.
	
	@argument client: what client are you fetching it from?
	@return: an array of integers.
	data[0]: Voltage Scaling High
	data[1]: Voltage Scaling Low
	data[2]: Current Scaling High
	data[3]: Current Scaling Low
	
	to use these numbers:
	Voltage scaling term, denoted as V_PU:
	V_PU = data[0] + data[1] * (2 ** -16)
	Current Scaling term, denoted as I_PU:
	I_PU = data[2] + data[3] * (2 ** -16)
	These numbers are the real scaling terms you must use.
	MODBUS is incapable of sending floating point numbers.
	
	"""
	data = checkForRegisters(client, 0x0000, 4, 100)
	return data

def retrieveADCVoltages(client, V_PU):
	"""
	# retreiveADCVoltages(): Retrives the filtered ADC voltages.
	# @argument client: what client are you asking?
	# @argument V_PU: the voltage scaling term.
	# @return: the filtered ADC voltage data.
	# data[0]: battery voltage
	# data[1]: battery voltage at terminal
	# data[2]: battery senser voltage
	# data[3]: array voltage
	"""
	data = checkForRegisters(client, 0x0018, 4, 100)
	if data == []: return []
	for i in range(4):
		data[i] *= (V_PU * (2 ** -15))
	return data

def retrieveADCCurrents(client, I_PU):
	"""
	#retrieveADCCurrents(): Retrieves the filtered ADC currents.
	# @argument client: what client are you asking?
	# @argument I_PU: the current scaling term. 
	# @return: the filtered ADC current data .
	# data[0]: battery current
	# data[1]: array current 
	"""
	data = checkForRegisters(client, 0x001C, 2, 100)
	for i in range(2):
		data[i] *= I_PU
		data[i] *= (2 ** -15)
	return data
def retrieveOtherVoltages(client):
	""" 
	#retrieveOtherVoltages(): retrives miscellaneous voltages.
	# @argumetn client: what client are you asking?
	# @return: the other ADC voltage data.
	# retrieved in this order:
	# 12 volt supply, 3 volt supply, meterbus voltage, 
	# 1.8 volt supply, reference voltage
	"""
	data = checkForRegisters(client, 0x001E, 5, 100)
	data[0] *= 18.612 * (2 ** -15)
	data[1] *= 6.6 * (2 ** -15) 
	data[2] *= 18.612 * (2 ** -15)
	data[3] *= 3 * (2 ** -15)
	data[4] *= 3 * (2 ** -15)
	return data

def retrieveTemperatures(client):
	"""
	#retrieveTemperatures(): retrives temperature values.
	# @argument client: what client are you asking?
	# @return: the temperatures.
	# gives it in this order: heatsink temperature, RTS temperature, battery regulation temperature.
	"""
	data = checkForRegisters(client, 0x0023, 3,100)
	return data

def retrieveSlowADC(client, V_PU, I_PU):
	"""
	#retriveSlowADC(): returns the slow values from the ADC. Tao = 1 minute.
	#@argument client: what client are you asking?
	#@arguments V_PU and I_PU: Voltage and Current scalers
	#@returns: slow values. Used for threshold values.
	# [battery voltage slow, charging current slow]
	"""
	data = checkForRegisters(client, 0x0026, 2, 100)
	data[0] *= V_PU * (2 ** -15)
	data[1] *= I_PU * (2 ** -15)
	return data

def retrieveMinMaxBatteryVoltages(client, V_PU):
	"""
	#retrieveHoursMinMaxBatteryVoltages(): 
	# returns the minimum and maximum battery voltages.
	# @argument client: what client are you asking?
	# @return: [minimum, maximum]
	"""
	data = checkForRegisters(client, 0x0028,2,100)
	for i in range(2): data[i] = (data[i] * (2 ** -15)) * V_PU
	return 

def retrieveHours(client):
	"""
	# retriveHours(): returns how many hours total it has been on.v
	# @argument client: what client are you asking?
	# @return: total hours the TSMMPT is on.
	"""
	data = checkForRegisters(client, 0x002A,2,100)
	result = (data[1] << 16) | data[0]
	return result
def retrieveControllerFaults(client):
	"""
	# retriveControllerFaults(): returns if there are any controller faults
	# @argument client: what client are you asking?
	# @return: list of faults as an array of strings describing each fault.
	"""
	data = checkForRegisters(client,0x002C, 1, 1000)
	bitfield = data[0]
	faultsTable = ["overcurrent", "FETs shorted","software bug",
	"battery HVD","array HVD","settings switch changed",
	"custom settings edit","RTS shorted","RTS disconnected",
	"EEPROM retry limit","N/A_10","Slave Control Timeout",
	"N/A_13","N/A_14","N/A_15","N/A_16"]
	result = []
	if not bitfield:
		return []
	for i in range(16):
		if bitfield & (0xFFFF & (0x1 << i)):
			result += faultsTable[i]
	return result

def retrieveAlarms(client):
	"""
	#retrieveAlarms(): tells you what alarms have been raised.
	# @argument client: what client are you asking?
	# @return: list of alarms raised. check MODBUS document for details.
	"""
	data = checkForRegisters(client,0x002E,2,1000)
	bitfield = (data[1] << 16)| data[0]
	alarmsTable = ["RTS open", "RTS shorted", "RTS disconnected", 
	"Heatsink temp sensor open", "Heatsink temp sensor shorted",
	"High temperature current limit", "Current limit", "Current offset",
	"Battery sense out of range", "Battery sense disconnected",
	"Uncalibrated", "RTS miswire", "High voltage disconnect",
	"Undefined", "System miswire", "MOSFET open", "P12 voltage off",
	"High input voltage current limit", "ADC input max",
	"Controller was reset", "N/A_21", "N/A_22", "N/A_23","N/A_24"]
	if not bitfield:
		return []
	result = []
	for i in range(24):
		if bitfield & (0x007FFFFF & (0x1 << i)):
			result.append(alarmsTable[i])
	return result

def retrieveDIPSwitch(client):
	"""
	#retrieveDIPSwitch(): returns the state of the DIP switch.
	# @argument client: what client are you asking?
	# @return array of 8 bits.
	"""
	data = checkForRegisters(client, 0x0030,1,100)
	bitfield = data[0]
	return bitfield
def retrieveLEDState(client):
	"""
	#retrieveLEDState(): tells you what state the LED is in.
	# @argument client: what client are you asking?
	# @return: string representing LED state.
	"""
	data = checkForRegisters(client, 0x0031,1,1000)
	value = data[0]
	if value == 0: return "LED START"
	elif value == 1: return "LED START 2"
	elif value == 2: return "LED BRANCH"
	elif value == 3: return "FAST GREEN BLINK"
	elif value == 4: return "SLOW GREEN BLINK"
	elif value == 5: return "GREEN BLINK, 1HZ"
	elif value == 6: return "GREEN LED"
	elif value == 7: return "UNDEFINED"
	elif value == 8: return "YELLOW LED"
	elif value == 9: return "UNDEFINED"
	elif value == 10: return "BLINKING RED LED"
	elif value == 11: return "RED LED"
	elif value == 12: return "R-Y-G ERROR"
	elif value == 13: return "R/Y-G ERROR"
	elif value == 14: return "R/G-Y ERROR"
	elif value == 15: return "R-Y ERROR (HTD)"
	elif value == 16: return "R-G ERROR (HVD)"
	elif value == 17: return "R/Y-G/Y ERROR"
	elif value == 18: return "G/Y/R ERROR"
	elif value == 19: return "G/Y/R X2"
	else: return "LED State value not recognized."

def retrieveChargeState(client):
	"""
	#retrieveChargeState(): reports the charge state of the battery
	# @argument client: what client are you asking?
	# @return: string that describes the charge state.
	"""
	data = checkForRegisters(client, 0x0032,1,1000)
	value = data[0]
	if value == 0: return "START"
	elif value == 1: return "NIGHT CHECK"
	elif value == 2: return "DISCONNECT"
	elif value == 3: return "NIGHT"
	elif value == 4: return "FAULT"
	elif value == 5: return "MPPT"
	elif value == 6: return "ABSORPTION"
	elif value == 7: return "FLOAT"
	elif value == 8: return "EQUALIZE"
	elif value == 9: return "SLAVE"
	else: return "Charge state value not recognized."

def retrieveChargeStatistics(client, V_PU):
	"""
	#retriveChargeStatistics(): returns charger statistics.
	# @argument client: what client are you asking?
	# @argument V_PU: voltage scaler.
	# @return: array.
	# [Target regulation voltage, Ah charge resettable, Ah charge total,
	# kWhr charge resettable, kWhr charge total]
	"""
	data = checkForRegisters(client, 0x0033, 7, 100)
	if data == []: return []
	else:
		vb_ref = data[0]*V_PU*(2**-15)
		Ahc_r = (data[1]*0.1 << 16) | data[2]
		Ahc_t = (data[3]*0.1 << 16) | data[4]
		kwhc_r = data[5]
		kwhc_t = data[6]
		return [vb_ref,Ahc_r, Ahc_t,kwhc_r,kwhc_t]

def retrieveMPPTStatistics(client, V_PU,I_PU):
	"""
	# retrieveMPPTStatistics(): returns MPPT statistics.
	# @argument client: what client are you asking?
	# @return: array.
	# [Output power, input power, max power of last sweep, 
	# Vmp of last sweep, Voc of last sweep]
	"""
	data = checkForRegisters(client, 0x003A, 5, 100)
	if data == []: return []
	else:
		p_out = data[0]*V_PU*I_PU*(2**-17)
		p_in = data[1]*V_PU*I_PU*(2**-17)
		p_max_sweep = data[2]*V_PU*I_PU*(2**-17)
		Vmp_sweep = data[3]*V_PU*(2**-15)
		Voc_sweep = data[4]*V_PU*(2**-15)
		return [p_out, p_in, p_max_sweep, Vmp_sweep, Voc_sweep]

def retrieveTodaysValues(client,V_PU, I_PU):
	"""
	#retrieveTodaysValues(): retrieve today's values.
	# @argument client: what client are you asking?	
	# @return: array.
	# [Minimum Daily Battery Voltage, Maximum Daily Battery Voltage, Maximum Daily input voltage,
	# Total Ah charge daily, Total Wh charge daily, Daily flags bitfield, 
	# Maximum power output daily, Minimum battery temperature dailyi, maximum temperature daily,
	# faults daily, daily alarms bitfield, cumulative time in absorption, daily,
	# cumulative time in equalize daily, cumulative time in float daily]
	"""
	data = checkForRegisters(client,0x0040, 16,100)
	try:
		vb_min_daily = data[0]*V_PU*(2**-15)
		vb_max_daily = data[1]*V_PU*(2**-15)
		vin_max_daily = data[2]*V_PU*(2**-15)
		Ahc_daily = data[3]*0.1
		whc_daily = data[4]
		dailyFlagsBitfield = data[5]
		Pout_max_daily = data[6]*V_PU*I_PU*(2**-17)
		Tb_min_daily = data[7]
		Tb_max_daily = data[8]
		dailyFaultsBitfield = data[9]
		dailyAlarmsBitfield = (data[11] << 16) | data[12]
		time_ab_daily = data[13]
		time_eq_daily = data[14]
		time_fl_daily = data[15]
		
		alarmsTable = ["RTS open", "RTS shorted", "RTS disconnected", 
		"Heatsink temp sensor open", "Heatsink temp sensor shorted",
		"High temperature current limit", "Current limit", "Current offset",
		"Battery sense out of range", "Battery sense disconnected",
		"Uncalibrated", "RTS miswire", "High voltage disconnect",
		"Undefined", "System miswire", "MOSFET open", "P12 voltage off",
		"High input voltage current limit", "ADC input max",
		"Controller was reset", "N/A_21", "N/A_22", "N/A_23","N/A_24"]
		dailyAlarms = []
		if dailyAlarmsBitfield:
			for i in range(24):
				if dailyAlarmsBitfield & (0x007FFFFF & (0x1 << i)):
					dailyAlarms += alarmsTable[i]
		flagsTable = ["Reset detected", "Equalize Triggered",
		"Enered float", "An alarm occurred", "A fault occurred"]
		dailyFlags = []
		if dailyFlagsBitfield:
			for i in range(5):
				if dailyFlagsBitfield & (0x1F & (0x1 << i)):
					dailyFlags += flagsTable[i]
		faultsTable = ["overcurrent", "FETs shorted","software bug",
		"battery HVD","array HVD","settings switch changed",
		"custom settings edit","RTS shorted","RTS disconnected",
		"EEPROM retry limit","N/A_10","Slave Control Timeout",
		"N/A_13","N/A_14","N/A_15","N/A_16"]
		dailyFaults = []
		if dailyFaultsBitfield:
			for i in range(9):
				if dailyFaultsBitfield & (0xFFFF & (0x1 << i)):
					dailyFaults += faultsTable[i]
					
		return [vb_min_daily, vb_max_daily, va_max_daily, Ahc_daily, whc_daily, 
		dailyFlags, Pout_max_daily, Tb_min_daily, Tb_max_daily, dailyFaults,
		dailyAlarms,time_ab_daily,time_eq_daily,time_fl_daily]
	except:
		return []
def checkChargeSettings(client, V_PU, I_PU):
	"""
	# Check EEPROM values.
	# checkChargeSettings(): returns an array full of charge settings. 
	# @argument client: what client are you reading?
	# @argument V_PU, I_PU: Voltage and Current Scaling.
	# @return: EEPROM Charge Settings. 
	# [absorption voltage at 25C, float voltage at 25C; 0 if disabled, absorption time,
	# absorption extension time, absorption extention threshold voltage,
	# voltage tha cancels float, exit float timer, Equalize V at 25C; 0 for disabled,
	# days between equalization cycles, equalize time limit above Vreg, equalize time limit at Veq,
	# Battery service timer, temperature compensation coefficient (negative assumed),
	# Battery High Voltage Disconnect, Battery High Voltage Reconnect, Battery charge reference limit,
	# max temperature compensation limit, min temperature compensation limit, LED threshold green to green/yellow,
	# LED threshold green/yellow to yellow, LED threshold yellow to yellow/red, LED threshold from yellow/red to red,
	# Battery Current Limit, Array V fixed target voltage, 
	# Array V fixed target V (% of Voc)]
	"""
	#data = checkForRegisters(client, 0xE000, 32, 10000)
	data1 = checkHoldingRegisters(client,0xE000,4,100)
	data2 = checkHoldingRegisters(client,0xE004,4,100)
	data3 = checkHoldingRegisters(client,0xE008,4,100)
	print(data1,data2,data3)
	data = checkHoldingRegisters(client,0xE000,32,100)
	try:
		EV_absorp = data[0]*V_PU*(2**-15)
		EV_float = data[1]*V_PU * (2 ** -15)
		Et_absorp = data[2]
		Et_absorp_ext = data[3]
		EV_absorp_ext = data[4]*V_PU * (2 ** -15)
		EV_float_cancel = data[5]*V_PU * (2 ** -15)
		Et_float_exit_cum = data[6]
		EV_eq = data[7]*V_PU * (2 ** -15)
		Et_eqcalendar = data[8]
		Et_eq_above = data[9]
		Et_eq_reg = data[10]
		Et_battery_service = data[11]
		EV_tempcomp = data[13]*V_PU * (2 ** -16)
		EV_hvd = data[14]*V_PU * (2 ** -15)
		EV_hvr = data[15]*V_PU * (2 ** -15)
		Evb_ref_lim = data[16]*V_PU * (2 ** -15)
		ETb_max = data[17]
		ETb_min = data[18]
		EV_soc_g_gy = data[21]*V_PU * (2 ** -15)
		EV_soc_gy_y = data[22]*V_PU * (2 ** -15)
		EV_soc_y_yr = data[23]*V_PU * (2 ** -15)
		EV_soc_yr_r = data[24]*V_PU * (2 ** -15)
		Elb_lim = data[29]*I_PU * (2 ** -15)
		EVa_ref_fixed_init = data[32] *V_PU * (2 ** -15)
		EVa_ref_fixed_pet_init = data[33]*100 * (2 ** -16)
		return [EV_absorp, EV_float, Et_absorp, Et_absorp_ext, EV_absorp_ext, 
		EV_float_cancel, Et_float_exit_cum, EV_eq, Et_eqcalendar, Et_eq_above, Et_eq_reg,
		Et_battery_service, EV_tempcomp, EV_hvd, EV_hvr, Evb_ref_lim, ETb_max, ETb_min,
		EV_soc_g_gy, EV_soc_gy_y, EV_soc_y_yr, EV_soc_yr_r, Elb_lim, EVa_ref_fixed_init, EVa_ref_fixed_pet_init]
	except:
		return []
