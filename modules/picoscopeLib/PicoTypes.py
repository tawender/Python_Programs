#****************************************************************************
#*
#* Filename:    ps4000Api.py
#* Copyright:
#* Author:      Toby Awender
#* Description:
#* This file defines the enumerated types used in calls to the ps4000.dll
#* for communication with the PicoScope4000 range of PC Oscilloscopes
#*
#****************************************************************************/
import ctypes







#****************************************************************************
#enumerated types contained in PS4000Imports.cs file from example project
#converted to dictionaries
#
#public enum Channel : int
Channel = {
    'ChannelA': 0,
    'ChannelB': 1,
    'ChannelC': 2,
    'ChannelD': 3,
    'External': 4,
    'Aux': 5,
    }

#public enum Range : int
Range = {
	'Range_10MV': 0,
	'Range_20MV': 1,
	'Range_50MV': 2,
	'Range_100MV': 3,
	'Range_200MV': 4,
	'Range_500MV': 5,
	'Range_1V': 6,
	'Range_2V': 7,
	'Range_5V': 8,
	'Range_10V': 9,
	'Range_20V': 10,
	'Range_50V': 11,
    'Range_100V': 12,
    }

#public enum ReportedTimeUnits : int
ReportedTimeUnits = {
	'FemtoSeconds': 0,
	'PicoSeconds': 1,
	'NanoSeconds': 2,
	'MicroSeconds': 3,
	'MilliSeconds': 4,
	'Seconds': 5,
    }

#public enum ThresholdMode : int
ThresholdMode = {
	'Level': 0,
	'Window': 1,
    }

#public enum ThresholdDirection : int
ThresholdDirection = {
	#Values for level threshold mode
	'Above': 0,
	'Below': 1,
	'Rising': 2,
	'Falling': 3,
	'RisingOrFalling': 4,

	#Values for window threshold mode
	'Inside': 0,
	'Outside': 1,
	'Enter': 2,
	'Exit': 3,
	'EnterOrExit': 4,
    #None = rising
    }

#public enum DownSamplingMode : int
DownSamplingMode = {
	#None = 0,
	'Aggregate': 0,
    }

#public enum PulseWidthType : int
PulseWidthType = {
	#None = 0,
	'LessThan': 1,
	'GreaterThan': 2,
	'InRange': 3,
	'OutOfRange': 4,
    }

#public enum TriggerState : int
TriggerState = {
	'DontCare': 0,
	'True': 1,
	'False': 2,
    }

#public enum Model : int
Model = {
    'NONE': 0,
    'PS4223': 4223,
    'PS4224': 4224,
    'PS4423': 4423,
    'PS4424': 4424,
    'PS4226': 4226,
    'PS4227': 4227,
    'PS4262': 4262,
    }
#
#end of the enumerated types contained in PS4000Imports.cs file from example project
#****************************************************************************










#****************************************************************************
#This section contains the constants and enumerated types from the header file ps4000Api.h
#
PS4000_MAX_OVERSAMPLE_12BIT = 16
PS4000_MAX_OVERSAMPLE_8BIT = 256

#Depending on the adc; oversample (collect multiple readings at each time) by up to 256.
#the results are therefore ALWAYS scaled up to 16-bits, even if
#oversampling is not used.
#
#The maximum and minimum values returned are therefore as follows:

PS4XXX_MAX_ETS_CYCLES = 400
PS4XXX_MAX_INTERLEAVE  = 80

PS4000_MAX_VALUE = 32764
PS4000_MIN_VALUE = -32764
PS4000_LOST_DATA = -32768

PS4000_EXT_MAX_VALUE = 32767
PS4000_EXT_MIN_VALUE = -32767

MAX_PULSE_WIDTH_QUALIFIER_COUNT = ctypes.c_long(16777215L).value
MAX_DELAY_COUNT = ctypes.c_long(8388607L).value

MIN_SIG_GEN_FREQ = 0.0
MAX_SIG_GEN_FREQ = 100000.0

MAX_SIG_GEN_BUFFER_SIZE = 8192
MIN_SIG_GEN_BUFFER_SIZE = 10
MIN_DWELL_COUNT	= 10
MAX_SWEEPS_SHOTS = ((1 << 30) - 1)

#typedef enum enChannelBufferIndex changed to dictionary
PS4000_CHANNEL_BUFFER_INDEX = {
	'PS4000_CHANNEL_A_MAX': 0,
	'PS4000_CHANNEL_A_MIN': 1,
	'PS4000_CHANNEL_B_MAX': 2,
	'PS4000_CHANNEL_B_MIN': 3,
	'PS4000_CHANNEL_C_MAX': 4,
	'PS4000_CHANNEL_C_MIN': 5,
	'PS4000_CHANNEL_D_MAX': 6,
	'PS4000_CHANNEL_D_MIN': 7,
	'PS4000_MAX_CHANNEL_BUFFERS': 8,
    }

#typedef enum enPS4000Channel changed to dictionary
PS4000_CHANNEL = {
	'PS4000_CHANNEL_A': 0,
	'PS4000_CHANNEL_B': 1,
	'PS4000_CHANNEL_C': 2,
	'PS4000_CHANNEL_D': 3,
	'PS4000_EXTERNAL': 4,
	'PS4000_MAX_CHANNELS': 4,
	'PS4000_TRIGGER_AUX': 5,
	'PS4000_MAX_TRIGGER_SOURCES': 6,
    }

#typedef enum enPS4000Range changed to dictionary
PS4000_RANGE = {
	'PS4000_10MV': 0,
	'PS4000_20MV': 1,
	'PS4000_50MV': 2,
	'PS4000_100MV': 3,
	'PS4000_200MV': 4,
	'PS4000_500MV': 5,
	'PS4000_1V': 6,
	'PS4000_2V': 7,
	'PS4000_5V': 8,
	'PS4000_10V': 9,
	'PS4000_20V': 10,
	'PS4000_50V': 11,
	'PS4000_100V': 12,
	'PS4000_MAX_RANGES': 13,

    'PS4000_RESISTANCE_100R': 13,
	'PS4000_RESISTANCE_1K': 14,
	'PS4000_RESISTANCE_10K': 15,
	'PS4000_RESISTANCE_100K': 16,
	'PS4000_RESISTANCE_1M': 17,
	'PS4000_MAX_RESISTANCES': 18,

	'PS4000_ACCELEROMETER_10MV': 18,
	'PS4000_ACCELEROMETER_20MV': 19,
	'PS4000_ACCELEROMETER_50MV': 20,
	'PS4000_ACCELEROMETER_100MV': 21,
	'PS4000_ACCELEROMETER_200MV': 22,
	'PS4000_ACCELEROMETER_500MV': 23,
	'PS4000_ACCELEROMETER_1V': 24,
	'PS4000_ACCELEROMETER_2V': 25,
	'PS4000_ACCELEROMETER_5V': 26,
	'PS4000_ACCELEROMETER_10V': 27,
	'PS4000_ACCELEROMETER_20V': 28,
	'PS4000_ACCELEROMETER_50V': 29,
	'PS4000_ACCELEROMETER_100V': 30,
	'PS4000_MAX_ACCELEROMETER': 31,

	'PS4000_TEMPERATURE_UPTO_40': 31,
	'PS4000_TEMPERATURE_UPTO_70': 32,
	'PS4000_TEMPERATURE_UPTO_100': 33,
	'PS4000_TEMPERATURE_UPTO_130': 34,
	'PS4000_MAX_TEMPERATURES': 35,

	'PS4000_RESISTANCE_5K': 36,
	'PS4000_RESISTANCE_25K': 37,
	'PS4000_RESISTANCE_50K': 38,
	'PS4000_MAX_EXTRA_RESISTANCES': 39,
    }

#typedef enum enPS4000Probe changed to dictionary
PS4000_PROBE = {
	'P_NONE': 0,
	'P_CURRENT_CLAMP_10A': 1,
	'P_CURRENT_CLAMP_1000A': 2,
	'P_TEMPERATURE_SENSOR': 3,
	'P_CURRENT_MEASURING_DEVICE': 4,
	'P_PRESSURE_SENSOR_50BAR': 5,
	'P_PRESSURE_SENSOR_5BAR': 6,
	'P_OPTICAL_SWITCH': 7,
	'P_UNKNOWN': 8,
	'P_MAX_PROBES': 8,
    }


#typedef enum enPS4000ChannelInfo
PS4000_CHANNEL_INFO = {
	'CI_RANGES': 0,
	'CI_RESISTANCES': 1,
	'CI_ACCELEROMETER': 2,
	'CI_PROBES': 3,
	'CI_TEMPERATURES': 4,
    }

#typedef enum enPS4000EtsMode
PS4000_ETS_MODE = {
    'PS4000_ETS_OFF': 0,             #ETS disabled
    'PS4000_ETS_FAST': 1,
	'PS4000_ETS_SLO': 2,
    'PS4000_ETS_MODES_MAX': 3,
    }

##typedef enum enPS4000TimeUnits
##  {
##  PS4000_FS,
##  PS4000_PS,
##  PS4000_NS,
##  PS4000_US,
##  PS4000_MS,
##  PS4000_S,
##  PS4000_MAX_TIME_UNITS,
##  }	PS4000_TIME_UNITS;
##
##typedef enum enSweepType
##{
##	UP,
##	DOWN,
##	UPDOWN,
##	DOWNUP,
##	MAX_SWEEP_TYPES
##} SWEEP_TYPE;
##
##typedef enum enWaveType
##{
##	PS4000_SINE,
##	PS4000_SQUARE,
##	PS4000_TRIANGLE,
##	PS4000_RAMP_UP,
##	PS4000_RAMP_DOWN,
##	PS4000_SINC,
##	PS4000_GAUSSIAN,
##	PS4000_HALF_SINE,
##	PS4000_DC_VOLTAGE,
##	PS4000_WHITE_NOISE,
##	MAX_WAVE_TYPES
##} WAVE_TYPE;
##
##typedef enum enSigGenTrigType
##{
##	SIGGEN_RISING,
##	SIGGEN_FALLING,
##	SIGGEN_GATE_HIGH,
##	SIGGEN_GATE_LOW
##} SIGGEN_TRIG_TYPE;
##
##typedef enum enSigGenTrigSource
##{
##	SIGGEN_NONE,
##	SIGGEN_SCOPE_TRIG,
##	SIGGEN_AUX_IN,
##	SIGGEN_EXT_IN,
##	SIGGEN_SOFT_TRIG
##} SIGGEN_TRIG_SOURCE;
##
##typedef enum enIndexMode
##{
##	SINGLE,
##	DUAL,
##	QUAD,
##	MAX_INDEX_MODES
##} INDEX_MODE;
##
##typedef enum enThresholdMode
##{
##	LEVEL,
##	WINDOW
##} THRESHOLD_MODE;
##
##typedef enum enThresholdDirection
##{
##	ABOVE, //using upper threshold
##	BELOW,
##	RISING, // using upper threshold
##	FALLING, // using upper threshold
##	RISING_OR_FALLING, // using both threshold
##	ABOVE_LOWER, // using lower threshold
##	BELOW_LOWER, // using lower threshold
##	RISING_LOWER,			 // using upper threshold
##	FALLING_LOWER,		 // using upper threshold
##
##	// Windowing using both thresholds
##	INSIDE = ABOVE,
##	OUTSIDE = BELOW,
##	ENTER = RISING,
##	EXIT = FALLING,
##	ENTER_OR_EXIT = RISING_OR_FALLING,
##	POSITIVE_RUNT = 9,
##  NEGATIVE_RUNT,
##
##	// no trigger set
##  NONE = RISING
##} THRESHOLD_DIRECTION;
##
##typedef enum enTriggerState
##{
##  CONDITION_DONT_CARE,
##  CONDITION_TRUE,
##  CONDITION_FALSE,
##	CONDITION_MAX
##} TRIGGER_STATE;
##
###pragma pack(1)
##typedef struct tTriggerConditions
##{
##  TRIGGER_STATE channelA;
##  TRIGGER_STATE channelB;
##  TRIGGER_STATE channelC;
##  TRIGGER_STATE channelD;
##  TRIGGER_STATE external;
##  TRIGGER_STATE aux;
##	TRIGGER_STATE pulseWidthQualifier;
##} TRIGGER_CONDITIONS;
###pragma pack()
##
###pragma pack(1)
##typedef struct tPwqConditions
##{
##  TRIGGER_STATE channelA;
##  TRIGGER_STATE channelB;
##  TRIGGER_STATE channelC;
##  TRIGGER_STATE channelD;
##  TRIGGER_STATE external;
##  TRIGGER_STATE aux;
##} PWQ_CONDITIONS;
###pragma pack()
##
###pragma pack(1)
##typedef struct tTriggerChannelProperties
##{
##  short thresholdUpper;
##	unsigned short thresholdUpperHysteresis;
##  short thresholdLower;
##	unsigned short thresholdLowerHysteresis;
##	PS4000_CHANNEL channel;
##  THRESHOLD_MODE thresholdMode;
##} TRIGGER_CHANNEL_PROPERTIES;
###pragma pack()
##
##typedef enum enRatioMode
##{
##	RATIO_MODE_NONE,
##	RATIO_MODE_AGGREGATE = 1,
##	RATIO_MODE_AVERAGE = 2
##} RATIO_MODE;
##
##typedef enum enPulseWidthType
##{
##	PW_TYPE_NONE,
##  PW_TYPE_LESS_THAN,
##	PW_TYPE_GREATER_THAN,
##	PW_TYPE_IN_RANGE,
##	PW_TYPE_OUT_OF_RANGE
##} PULSE_WIDTH_TYPE;
##
##typedef enum enPs4000HoldOffType
##{
##	PS4000_TIME,
##	PS4000_MAX_HOLDOFF_TYPE
##} PS4000_HOLDOFF_TYPE;
##
##typedef enum enPS4000FrequencyCounterRange
##{
##  FC_2K,
##  FC_20K,
##  FC_MAX
##}PS4000_FREQUENCY_COUNTER_RANGE;
##
##typedef void (__stdcall *ps4000BlockReady)
##	(
##		short											handle,
##		PICO_STATUS								status,
##		void										*	pParameter
##	);
##
##typedef void (__stdcall *ps4000StreamingReady)
##	(
##		short    									handle,
##		long     									noOfSamples,
##		unsigned long							startIndex,
##		short    									overflow,
##		unsigned long							triggerAt,
##		short    									triggered,
##		short    									autoStop,
##		void										*	pParameter
##	);
##
##typedef void (__stdcall *ps4000DataReady)
##	(
##		short    									handle,
##		long     									noOfSamples,
##		short    									overflow,
##		unsigned long							triggerAt,
##		short    									triggered,
##		void										*	pParameter
##	);
###
###End of constants and enumerated types from the header file ps4000Api.h
###****************************************************************************
