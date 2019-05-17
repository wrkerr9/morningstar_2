
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
			returns this array:
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
		data[6] *= I_PU * (2 ** -15)
		data[7] *= 18.612 * (2 ** -15)
		data[8] *= 6.6 * (2 ** -15)
		data[9] *= 18.612 * (2 ** -15)
		data[10] *= 3 * (2 ** -15)
		data[11] *= 3 * (2 ** -15)		
		return data
	def TemperatureData(self):
		"""
			returns this array:
			[Heatsink temperature, RTS temperature, Battery Regulation Temperature]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0023,3)
		return data
	def StatusData(self)
		""" 
		returns this array:
		[battery_voltage,charging_current,min_battery_voltage,max_battery_voltage,
		hourmeter,faults,alarms,dipswitch_bitfield,ledvalue]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0026,12)
		battery_voltage = data[0] * self.V_PU * (2 ** -15)
		charging_current = data[1] * self.I_PU * (2 ** -15)
		min_battery_voltage = data[2] * sefl.V_PU * (2 ** -15)
		max_battery_voltage = data[3] * sefl.V_PU * (2 ** -15)
		hourmeter  = data[5] | data[4] << 16
		bitfield = data[6]
		
		#faults status
		faultsTable = ["overcurrent", "FETs shorted","software bug",
		"battery HVD","array HVD","settings switch changed",
		"custom settings edit","RTS shorted","RTS disconnected",
		"EEPROM retry limit","N/A_10","Slave Control Timeout",
		"N/A_13","N/A_14","N/A_15","N/A_16"]
		faults = []
		if bitfield:
			for i in range(16):
				if bitfield & (0xFFFF & (0x1 << i)):
					faults.append(faultsTable[i])
					
	
		bitfield = (data[9] << 16)| data[8]
		alarmsTable = ["RTS open", "RTS shorted", "RTS disconnected", 
		"Heatsink temp sensor open", "Heatsink temp sensor shorted",
		"High temperature current limit", "Current limit", "Current offset",
		"Battery sense out of range", "Battery sense disconnected",
		"Uncalibrated", "RTS miswire", "High voltage disconnect",
		"Undefined", "System miswire", "MOSFET open", "P12 voltage off",
		"High input voltage current limit", "ADC input max",
		"Controller was reset", "N/A_21", "N/A_22", "N/A_23","N/A_24"]
		alarms = []
		if bitfield:
			for i in range(24):
				if bitfield & (0x007FFFFF & (0x1 << i)):
					alarms.append(alarmsTable[i])	
		dipswitch = data[10]
		
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
		dipswitch_bitfield = dipswitch 
		
		return [battery_voltage,charging_current,min_battery_voltage,max_battery_voltage,
		hourmeter,faults,alarms,dipswitch_bitfield,ledvalue]
	def ChargerData(self):
		"""
			returns this array:
			[chargeState, targetRegVoltage, AhChargeResettable, AhChargeTotal, kWhrChargeResettable, kWhrChargeTotal ]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0032, 8)
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
		targetRegVoltage = data[1]
		AhChargeResettable = (data[3] | data[2] << 16)*0.1
		AhChargeTotal = (data[5] | data[4] << 16)*0.1
		kWhrChargeResettable = data[6]
		kWhrChargeTotal = data[7]
		return [chargeState, targetRegVoltage, AhChargeResettable, AhChargeTotal, kWhrChargeResettable, kWhrChargeTotal ]
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
		return data
	def Logger_TodaysValues(self):
		"""
			returns this array:
			[vb_min_daily, vb_max_daily, va_max_daily, Ahc_daily, whc_daily, 
		dailyFlags, Pout_max_daily, Tb_min_daily, Tb_max_daily, dailyFaults,
		dailyAlarms,time_ab_daily,time_eq_daily,time_fl_daily]
		
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_HOLDING_REGISTERS, 0x0040, 16)
		
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
	def ChargeSettings(self):
		"""
			returns this array;
			[EV_absorp, EV_float, Et_absorp, Et_absorp_ext, EV_absorp_ext, 
			EV_float_cancel, Et_float_exit_cum, EV_eq, Et_eqcalendar, Et_eq_above, Et_eq_reg,
			Et_battery_service, EV_tempcomp, EV_hvd, EV_hvr, Evb_ref_lim, ETb_max, ETb_min,
			EV_soc_g_gy, EV_soc_gy_y, EV_soc_y_yr, EV_soc_yr_r, Elb_lim, EVa_ref_fixed_init, EVa_ref_fixed_pet_init]
		"""
		data = self.master.execute(self.SLAVE_NUMBER, cst.READ_INPUT_REGISTERS, 0xE000, 32)
		
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
	def DumpDataToJSONFile(self):
		ADC = self.ADCdata()
		#converts the list to a tuple and assigns varaibles.
		bv,bv_t, bv_s,av,bc,ac,v_12,v_3,mb_v,v_1_8,v_ref = tuple(ADC)
		
		Temp = self.TemperatureData()
		T_hs,T_rts,T_batt = tuple(Temp)
		
		Status = self.StatusData()
		bv_1_min,bc_1_min,bv_min,bv_max,hourmeter,controller_faults,alarms,
		DIP,LED_status = tuple(Status)
		
		Charger = self.ChargerData()
		charge_state,vb_ref, Ahc_r, Ahc_t, kwhc_r,kwhc_t = tuple(Charger)
		
		MPPT = self.MPPTData()
		p_out,p_in,p_max_sweep, v_mp_sweep, v_oc_sweep = tuple(MPPT)
		
		Logger = self.Logger_TodaysValues()
		vb_min_daily, vb_max_daily, va_max_daily, Ahc_daily, whc_daily, 
		dailyFlags, Pout_max_daily, Tb_min_daily, Tb_max_daily, dailyFaults,
		dailyAlarms,time_ab_daily,time_eq_daily,time_fl_daily = tuple(Logger)
		
		
		ChargeSettings = self.ChargeSettings()
		EV_absorp, EV_float, Et_absorp, Et_absorp_ext, EV_absorp_ext, 
		EV_float_cancel, Et_float_exit_cum, EV_eq, Et_eqcalendar, Et_eq_above, Et_eq_reg,
		Et_battery_service, EV_tempcomp, EV_hvd, EV_hvr, Evb_ref_lim, ETb_max, ETb_min,
		EV_soc_g_gy, EV_soc_gy_y, EV_soc_y_yr, EV_soc_yr_r, Elb_lim, EVa_ref_fixed_init, EVa_ref_fixed_pet_init = tuple(ChargeSettings)
		
		
		JSON_file = json.dumps( 
			{
				'Battery Voltage': bv,
				'Battery Terminal Voltage': bv_t,
				'Battery Sense Voltage': bv_s,
				'Array Voltage': av,
				'Battery Current': bc,
				'Array Current': ac,
				'12 volt supply': v_12,
				'3 volt supply': v_3,
				'MeterBus voltage': mb_v,
				'1.8 volt supply': v_1_8,
				'Reference Voltage': v_ref,
				
				'Heatsink Temperature': T_hs,
				'RTS Temperature': T_rts,
				'Battery Regulation Temperature': T_batt,
				
				'Battery Voltage slow': bv_1_min,
				'Charging Current slow': bc_1_min,
				'Minimum Battery Voltage': bv_min,
				'Maximum Battery Voltage': bv_max,
				'Hourmeter': hourmeter,
				'Controller Faults': controller_faults,
				'Alarms': alarms,
				'DIP Switch Positions': DIP,
				'LED status': LED_status,
				
				'Charging State': charge_state,
				'Target Regulation Voltage': vb_ref,
				'Ah Charge - Resetable': Ahc_r,
				'Ah Charge - Total': Ahc_t,
				'kWhr charge - Resetable': kwhc_r,
				'kWhr charge - Total': kwhc_t,
				
				'MPPT Output Power': p_out,
				'MPPT Input Power': p_in,
				'Max power of last sweep': p_max_sweep,
				'Vmp of last sweep': v_mp_sweep,
				'Voc of last sweep': v_oc_sweep,
				
				'Today\'s Values:': Logger,
				'Charge Settings:': ChargeSettings
			}
		)
		return JSON_file

if __name__ == '__main__':	
	try:
		firstMorningstarString = Morningstar("COM4", 9600, 0x1)
		secondMorningstarString = Morningstar("COM5", 9600, 0x1)
		f1 = firstMorningstarString.DumpDataToJSONFile()
		f2 = secondMorningstarString.DumpDataToJSONFile()
		print(f1)
		print(f2)
	except:
		pass


