
import json
import serial

import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

from morningstar_lib import *


class Morningstar(self):
	#variables:
	#PORT number
	#BAUD
	#SLAVE_NUMBER
	#serial connection
	#modbus connection
	#voltage scaler (V_PU)
	#current scaler (I_PU)
	
	def __init__(self,PORT,baudrate,SLAVE_NUMBER):
		self.PORT = PORT
		self.BAUD = baudrate
		self.SLAVE_NUMBER = SLAVE_NUMBER
		self.serial_connection = serial.Serial(port=PORT, baudrate=baudrate, bytesize=8, parity='N',xonxoff = 0)
		self.master = modbus_rtu.RtuMaster(self.s_connection)
		self.scaling()
	def scaling(self):	
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0000, 5)
		self.V_PU = data[0] + data[1] * (2 ** -15)
		self.I_PU = data[2] + data[3] * (2 ** -15)
		print("Running version", data[4])
	def ADCdata(self):
		"""
			returns this dictionary
			[battery voltage, battery terminal voltage, battery sense voltage, array voltage,
			battery current, array current, 12V supply, 3V supply, meterbus voltage,
			1.8V supply, reference voltage]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0018, 11)
		data[0] *= V_PU * (2 ** -15)
		data[1] *= V_PU * (2 ** -15)
		data[2] *= V_PU * (2 ** -15)
		data[3] *= V_PU * (2 ** -15)
		data[4] *= I_PU * (2 ** -15)
		data[5] *= I_PU * (2 ** -15)
		data[6] *= 18.612 * (2 ** -15)
		data[7] *= 6.6 * (2 ** -15)
		data[8] *= 18.612 * (2 ** -15)
		data[9] *= 3 * (2 ** -15)
		data[10] *= 3 * (2 ** -15)	

		records = {}
		records['battery voltage'] = data[0]
		records['battery terminal voltage']= data[1]
		records['battery sense voltage'] = data[2]
		records['array voltage']= data[3]
		records['battery current'] = data[4]
		records['array current']= data[5] 
		records['12V supply'] = data[6]
		records['3V supply'] = data[7]
		records['meterbus voltage']= data[8]
		records['1.8V supply'] = data[9]
		records['reference voltage']= data[10]
		return records
	def TemperatureData(self):
		"""
			returns this array:
			[Heatsink temperature, RTS temperature, Battery Regulation Temperature]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0023,3)
		records = {}
		records['heatsink temperature'] = data[0]
		records['RTS temperature'] = data[1]
		records['battery regulation temperature'] = data[2]
		return records
	def StatusData(self)
		""" 
		returns this array:
		[battery_voltage,charging_current,min_battery_voltage,max_battery_voltage,
		hourmeter,faults,alarms,dipswitch_bitfield,ledvalue]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0026,12)
		records = {}
		
		records['battery_voltage'] = data[0] * self.V_PU * (2 ** -15)
		records['charging_current'] = data[1] * self.I_PU * (2 ** -15)
		records['minimum battery voltage'] = data[2] * self.V_PU * (2 ** -15)
		records['maximum battery voltage'] = data[3] * self.V_PU * (2 ** -15)
		records['hourmeter']  = data[5] | data[4] << 16
		bitfield = data[6]
		
		#faults status
		faultsTable = ["overcurrent", "FETs shorted","software bug",
		"battery HVD","array HVD","settings switch changed",
		"custom settings edit","RTS shorted","RTS disconnected",
		"EEPROM retry limit","N/A_10","Slave Control Timeout",
		"N/A_13","N/A_14","N/A_15","N/A_16"]
		faults = ""
		if bitfield:
			for i in range(16):
				if bitfield & (0xFFFF & (0x1 << i)):
					faults += faultsTable[i] + ", "
		records['faults'] = faults			
	
		bitfield = (data[9] << 16)| data[8]
		alarmsTable = ["RTS open", "RTS shorted", "RTS disconnected", 
		"Heatsink temp sensor open", "Heatsink temp sensor shorted",
		"High temperature current limit", "Current limit", "Current offset",
		"Battery sense out of range", "Battery sense disconnected",
		"Uncalibrated", "RTS miswire", "High voltage disconnect",
		"Undefined", "System miswire", "MOSFET open", "P12 voltage off",
		"High input voltage current limit", "ADC input max",
		"Controller was reset", "N/A_21", "N/A_22", "N/A_23","N/A_24"]
		alarms = ""
		if bitfield:
			for i in range(24):
				if bitfield & (0x007FFFFF & (0x1 << i)):
					alarms += alarmsTable[i] + ", "	
		records['alarms'] = alarms
		dipswitch = data[10]
		dipSwitchStatement = ""
		for i in range(8):
			if dipswitch & (0x1 << i):
				dipSwitchStatement += "ON "
			else:
				dipSwitchStatement += "OFF "
		records['DIP switch status'] = dipSwitchStatement
		ledvalue = data[11]
		ledstate = ""
		if ledvalue == 0: ledstate =  "LED START"
		elif ledvalue == 1: ledstate =  "LED START 2"
		elif ledvalue == 2: ledstate =  "LED BRANCH"
		elif ledvalue == 3: ledstate =  "FAST GREEN BLINK"
		elif ledvalue == 4: ledstate =  "SLOW GREEN BLINK"
		elif ledvalue == 5: ledstate =  "GREEN BLINK, 1HZ"
		elif ledvalue == 6: ledstate =  "GREEN LED"
		elif ledvalue == 7: ledstate =  "UNDEFINED"
		elif ledvalue == 8: ledstate =  "YELLOW LED"
		elif ledvalue == 9: ledstate =  "UNDEFINED"
		elif ledvalue == 10: ledstate =  "BLINKING RED LED"
		elif ledvalue == 11: ledstate =  "RED LED"
		elif ledvalue == 12: ledstate =  "R-Y-G ERROR"
		elif ledvalue == 13: ledstate =  "R/Y-G ERROR"
		elif ledvalue == 14: ledstate =  "R/G-Y ERROR"
		elif ledvalue == 15: ledstate =  "R-Y ERROR (HTD)"
		elif ledvalue == 16: ledstate =  "R-G ERROR (HVD)"
		elif ledvalue == 17: ledstate =  "R/Y-G/Y ERROR"
		elif ledvalue == 18: ledstate =  "G/Y/R ERROR"
		elif ledvalue == 19: ledstate =  "G/Y/R X2"
		else: ledstate =  "LED State value not recognized."
		records['LED state'] = ledstate
		
		return records
	def ChargerData(self):
		"""
			returns this dictionary:
			[chargeState, targetRegVoltage, AhChargeResettable, AhChargeTotal, kWhrChargeResettable, kWhrChargeTotal ]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0032, 8)
		records = {}
		chargerValue = data[0]
		chargeState = ""
		if chargerValue == 0: chargeState =  "START"
		elif chargerValue == 1: chargeState =  "NIGHT CHECK"
		elif chargerValue == 2: chargeState =  "DISCONNECT"
		elif chargerValue == 3: chargeState =  "NIGHT"
		elif chargerValue == 4: chargeState =  "FAULT"
		elif chargerValue == 5: chargeState =  "MPPT"
		elif chargerValue == 6: chargeState =  "ABSORPTION"
		elif chargerValue == 7: chargeState =  "FLOAT"
		elif chargerValue == 8: chargeState =  "EQUALIZE"
		elif chargerValue == 9: chargeState =  "SLAVE"
		else: chargeState =  "Charge state value not recognized."
		records['Charge State'] = chargeState
		
		records['target regulatoin voltage'] = data[1]
		records['Ah Charge Resettable'] = (data[3] | data[2] << 16)*0.1
		records['Ah Charge Total'] = (data[5] | data[4] << 16)*0.1
		records['kWhr Charge Resettable'] = data[6]
		records['kWhr Charge Total'] = data[7]
		return records
	def MPPTData(self):
		"""
			returns this array:
			[output power, input power, max power of last sweep,
			Vmp of last sweep, Voc of last sweep]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x003A, 5)
		data[0] *= self.V_PU * self.I_PU * (2 ** -17)
		data[1] *= self.V_PU * self.I_PU * (2 ** -17)
		data[2] *= self.V_PU * self.I_PU * (2 ** -17)
		data[3] *= self.V_PU * (2 ** -15)
		data[4] *= self.V_PU * (2 ** -15)
		records = {}
		records['output power'] = data[0]
		records['input power'] = data[1]
		records['max power of last sweep'] = data[2]
		records['Vmp of last sweep'] = data[3]
		records['Voc of last sweep'] = data[4]
		return records
	def Logger_TodaysValues(self):
		"""
			returns this array:
			[vb_min_daily, vb_max_daily, va_max_daily, Ahc_daily, whc_daily, 
		dailyFlags, Pout_max_daily, Tb_min_daily, Tb_max_daily, dailyFaults,
		dailyAlarms,time_ab_daily,time_eq_daily,time_fl_daily]
		
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0040, 16)
		records = {}
		
		records['Battery Voltage Minimum Daily'] = data[0]*V_PU*(2**-15)
		records['Battery Voltage Maximum Daily'] = data[1]*V_PU*(2**-15)
		records['Input Voltage Maximum Daily'] = data[2]*V_PU*(2**-15)
		records['Amp Hours accumulated daily'] = data[3]*0.1
		records['Watt Hours accumulated daily'] = data[4]
		dailyFlagsBitfield = data[5]
		records['Maximum power output daily'] = data[6]*V_PU*I_PU*(2**-17)
		records['Minimum temperature daily'] = data[7]
		records['Maximum temperature daily'] = data[8]
		dailyFaultsBitfield = data[9]
		dailyAlarmsBitfield = (data[11] << 16) | data[12]
		records['time_ab_daily'] = data[13]
		records['time_eq_daily'] = data[14]
		records['time_fl_daily'] = data[15]
		
		alarmsTable = ["RTS open", "RTS shorted", "RTS disconnected", 
		"Heatsink temp sensor open", "Heatsink temp sensor shorted",
		"High temperature current limit", "Current limit", "Current offset",
		"Battery sense out of range", "Battery sense disconnected",
		"Uncalibrated", "RTS miswire", "High voltage disconnect",
		"Undefined", "System miswire", "MOSFET open", "P12 voltage off",
		"High input voltage current limit", "ADC input max",
		"Controller was reset", "N/A_21", "N/A_22", "N/A_23","N/A_24"]
		dailyAlarms = ""
		if dailyAlarmsBitfield:
			for i in range(24):
				if dailyAlarmsBitfield & (0x007FFFFF & (0x1 << i)):
					dailyAlarms += alarmsTable[i]
		records['daily alarms'] = dailyAlarms
		
		flagsTable = ["Reset detected", "Equalize Triggered",
		"Enered float", "An alarm occurred", "A fault occurred"]
		dailyFlags = ""
		if dailyFlagsBitfield:
			for i in range(5):
				if dailyFlagsBitfield & (0x1F & (0x1 << i)):
					dailyFlags += flagsTable[i]
		records['daily flags'] = dailyFlags
		
		faultsTable = ["overcurrent", "FETs shorted","software bug",
		"battery HVD","array HVD","settings switch changed",
		"custom settings edit","RTS shorted","RTS disconnected",
		"EEPROM retry limit","N/A_10","Slave Control Timeout",
		"N/A_13","N/A_14","N/A_15","N/A_16"]
		dailyFaults = ""
		if dailyFaultsBitfield:
			for i in range(9):
				if dailyFaultsBitfield & (0xFFFF & (0x1 << i)):
					dailyFaults += faultsTable[i]
		records['daily faults'] = dailyFaults		
		return records
	def ChargeSettings(self):
		"""
			returns this array;
			[EV_absorp, EV_float, Et_absorp, Et_absorp_ext, EV_absorp_ext, 
			EV_float_cancel, Et_float_exit_cum, EV_eq, Et_eqcalendar, Et_eq_above, Et_eq_reg,
			Et_battery_service, EV_tempcomp, EV_hvd, EV_hvr, Evb_ref_lim, ETb_max, ETb_min,
			EV_soc_g_gy, EV_soc_gy_y, EV_soc_y_yr, EV_soc_yr_r, Elb_lim, EVa_ref_fixed_init, EVa_ref_fixed_pet_init]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_INPUT_REGISTERS, 0xE000, 32)
		records = {}
		records['EV_absorp'] = data[0]*V_PU*(2**-15)
		records['EV_float'] = data[1]*V_PU * (2 ** -15)
		records['Et_absorp'] = data[2]
		records['Et_absorp_ext'] = data[3]
		records['EV_absorp_ext'] = data[4]*V_PU * (2 ** -15)
		records['EV_float_cancel'] = data[5]*V_PU * (2 ** -15)
		records['Et_float_exit_cum'] = data[6]
		records['EV_eq'] = data[7]*V_PU * (2 ** -15)
		records['Et_eqcalendar'] = data[8]
		records['Et_eq_above'] = data[9]
		records['Et_eq_reg'] = data[10]
		records['Et_battery_service'] = data[11]
		records['EV_tempcomp'] = data[13]*V_PU * (2 ** -16)
		records['EV_hvd'] = data[14]*V_PU * (2 ** -15)
		records['EV_hvr'] = data[15]*V_PU * (2 ** -15)
		records['Evb_ref_lim'] = data[16]*V_PU * (2 ** -15)
		records['ETb_max'] = data[17]
		records['ETb_min'] = data[18]
		records['EV_soc_g_gy'] = data[21]*V_PU * (2 ** -15)
		records['EV_soc_gy_y'] = data[22]*V_PU * (2 ** -15)
		records['EV_soc_y_yr'] = data[23]*V_PU * (2 ** -15)
		records['EV_soc_yr_r'] = data[24]*V_PU * (2 ** -15)
		records['Elb_lim'] = data[29]*I_PU * (2 ** -15)
		records['EVa_ref_fixed_init'] = data[32] *V_PU * (2 ** -15)
		records['EVa_ref_fixed_pet_init'] = data[33]*100 * (2 ** -16)
		return records
	def DumpInstantenousDataToJSONFile(self,outfile):
		ADC = self.ADCdata()
		Temp = self.TemperatureData()
		Status = self.StatusData()
		Charger = self.ChargerData()
		MPPT = self.MPPTData()
		
		data = {}
		data['ADC data'] = ADC
		data['Temperature data'] = Temp
		data['Status'] = Status
		data['Charger Data'] = Charger
		data['MPPT Data'] = MPPT
		import json
		json.dumps(outfile,data)

	def DumpDailyDataToJSONFile(self,outfile):
		Logger = self.Logger_TodaysValues()
		ChargeSettings = self.ChargeSettings()
		data = {}
		data['Daily Logger Values'] = Logger
		data['Charge Settings'] = ChargeSettings
		import json
		json.dumps(outfile,data)
if __name__ == '__main__':	
	try:
		firstMorningstarString = Morningstar("COM4", 9600, 0x1)
		secondMorningstarString = Morningstar("COM5", 9600, 0x1)
		f1 = open("test.json","rw")
		f2 = open("test_daily.json", "rw")
		f3 = open("test1.json", "rw")
		f4 = open("test1_daily.json", "rw")
		firstMorningstarString.DumpDailyDataToJSONFile(f2)
		firstMorningstarString.DumpInstantenousDataToJSONFile(f1)
		secondMorningstarString.DumpDailyDataToJSONFile(f4)
		secondMorningstarString.DumpInstantenousDataToJSONFile(f3)
	
	except:
		pass
