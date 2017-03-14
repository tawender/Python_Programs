import ctypes

unit_info = {
	'PICO_DRIVER_VERSION' : ctypes.c_ulong(0x00000000).value,
	'PICO_USB_VERSION' : ctypes.c_ulong(0x00000001).value,
	'PICO_HARDWARE_VERSION' : ctypes.c_ulong(0x00000002).value,
	'PICO_VARIANT_INFO' : ctypes.c_ulong(0x00000003).value,
	'PICO_BATCH_AND_SERIAL' : ctypes.c_ulong(0x00000004).value,
	'PICO_CAL_DATE' : ctypes.c_ulong(0x00000005).value,
	'PICO_KERNEL_VERSION' : ctypes.c_ulong(0x00000006).value,
	'PICO_DIGITAL_HARDWARE_VERSION' : ctypes.c_ulong(0x00000007).value,
	'PICO_ANALOGUE_HARDWARE_VERSION' : ctypes.c_ulong(0x00000008).value,
	'PICO_FIRMWARE_VERSION_1' : ctypes.c_ulong(0x00000009).value,
	'PICO_FIRMWARE_VERSION_2' : ctypes.c_ulong(0x0000000A).value,
	'PICO_MAC_ADDRESS' : ctypes.c_ulong(0x0000000B).value,
    }

constants = {
	'PICO_OK' : ctypes.c_ulong(0x00000000).value,
	'PICO_MAX_UNITS_OPENED' : ctypes.c_ulong(0x00000001).value,
	'PICO_MEMORY_FAIL' : ctypes.c_ulong(0x00000002).value,
	'PICO_NOT_FOUND' : ctypes.c_ulong(0x00000003).value,
	'PICO_FW_FAIL' : ctypes.c_ulong(0x00000004).value,
	'PICO_OPEN_OPERATION_IN_PROGRESS' : ctypes.c_ulong(0x00000005).value,
	'PICO_OPERATION_FAILED' : ctypes.c_ulong(0x00000006).value,
	'PICO_NOT_RESPONDING' : ctypes.c_ulong(0x00000007).value,
	'PICO_CONFIG_FAIL' : ctypes.c_ulong(0x00000008).value,
	'PICO_KERNEL_DRIVER_TOO_OLD' : ctypes.c_ulong(0x00000009).value,
	'PICO_EEPROM_CORRUPT' : ctypes.c_ulong(0x0000000A).value,
	'PICO_OS_NOT_SUPPORTED' : ctypes.c_ulong(0x0000000B).value,
	'PICO_INVALID_HANDLE' : ctypes.c_ulong(0x0000000C).value,
	'PICO_INVALID_PARAMETER' : ctypes.c_ulong(0x0000000D).value,
	'PICO_INVALID_TIMEBASE' : ctypes.c_ulong(0x0000000E).value,
	'PICO_INVALID_VOLTAGE_RANGE' : ctypes.c_ulong(0x0000000F).value,
	'PICO_INVALID_CHANNEL' : ctypes.c_ulong(0x00000010).value,
	'PICO_INVALID_TRIGGER_CHANNEL' : ctypes.c_ulong(0x00000011).value,
	'PICO_INVALID_CONDITION_CHANNEL' : ctypes.c_ulong(0x00000012).value,
	'PICO_NO_SIGNAL_GENERATOR' : ctypes.c_ulong(0x00000013).value,
	'PICO_STREAMING_FAILED' : ctypes.c_ulong(0x00000014).value,
	'PICO_BLOCK_MODE_FAILED' : ctypes.c_ulong(0x00000015).value,
	'PICO_NULL_PARAMETER' : ctypes.c_ulong(0x00000016).value,
	'PICO_ETS_MODE_SET' : ctypes.c_ulong(0x00000017).value,
	'PICO_DATA_NOT_AVAILABLE' : ctypes.c_ulong(0x00000018).value,
	'PICO_STRING_BUFFER_TO_SMALL' : ctypes.c_ulong(0x00000019).value,
	'PICO_ETS_NOT_SUPPORTED' : ctypes.c_ulong(0x0000001A).value,
	'PICO_AUTO_TRIGGER_TIME_TO_SHORT' : ctypes.c_ulong(0x0000001B).value,
	'PICO_BUFFER_STALL' : ctypes.c_ulong(0x0000001C).value,
	'PICO_TOO_MANY_SAMPLES' : ctypes.c_ulong(0x0000001D).value,
	'PICO_TOO_MANY_SEGMENTS' : ctypes.c_ulong(0x0000001E).value,
	'PICO_PULSE_WIDTH_QUALIFIER' : ctypes.c_ulong(0x0000001F).value,
	'PICO_DELAY' : ctypes.c_ulong(0x00000020).value,
	'PICO_SOURCE_DETAILS' : ctypes.c_ulong(0x00000021).value,
	'PICO_CONDITIONS' : ctypes.c_ulong(0x00000022).value,
	'PICO_USER_CALLBACK' : ctypes.c_ulong(0x00000023).value,
	'PICO_DEVICE_SAMPLING' : ctypes.c_ulong(0x00000024).value,
	'PICO_NO_SAMPLES_AVAILABLE' : ctypes.c_ulong(0x00000025).value,
	'PICO_SEGMENT_OUT_OF_RANGE' : ctypes.c_ulong(0x00000026).value,
	'PICO_BUSY' : ctypes.c_ulong(0x00000027).value,
	'PICO_STARTINDEX_INVALID' : ctypes.c_ulong(0x00000028).value,
	'PICO_INVALID_INFO' : ctypes.c_ulong(0x00000029).value,
	'PICO_INFO_UNAVAILABLE' : ctypes.c_ulong(0x0000002A).value,
	'PICO_INVALID_SAMPLE_INTERVAL' : ctypes.c_ulong(0x0000002B).value,
	'PICO_TRIGGER_ERROR' : ctypes.c_ulong(0x0000002C).value,
	'PICO_MEMORY' : ctypes.c_ulong(0x0000002D).value,
	'PICO_SIG_GEN_PARAM' : ctypes.c_ulong(0x0000002E).value,
	'PICO_SHOTS_SWEEPS_WARNING' : ctypes.c_ulong(0x0000002F).value,
	'PICO_SIGGEN_TRIGGER_SOURCE' : ctypes.c_ulong(0x00000030).value,
	'PICO_AUX_OUTPUT_CONFLICT' : ctypes.c_ulong(0x00000031).value,
	'PICO_AUX_OUTPUT_ETS_CONFLICT' : ctypes.c_ulong(0x00000032).value,
	'PICO_WARNING_EXT_THRESHOLD_CONFLICT' : ctypes.c_ulong(0x00000033).value,
	'PICO_WARNING_AUX_OUTPUT_CONFLICT' : ctypes.c_ulong(0x00000034).value,
	'PICO_SIGGEN_OUTPUT_OVER_VOLTAGE' : ctypes.c_ulong(0x00000035).value,
	'PICO_DELAY_NULL' : ctypes.c_ulong(0x00000036).value,
	'PICO_INVALID_BUFFER' : ctypes.c_ulong(0x00000037).value,
	'PICO_SIGGEN_OFFSET_VOLTAGE' : ctypes.c_ulong(0x00000038).value,
	'PICO_SIGGEN_PK_TO_PK' : ctypes.c_ulong(0x00000039).value,
	'PICO_CANCELLED' : ctypes.c_ulong(0x0000003A).value,
	'PICO_SEGMENT_NOT_USED' : ctypes.c_ulong(0x0000003B).value,
	'PICO_INVALID_CALL' : ctypes.c_ulong(0x0000003C).value,
	'PICO_GET_VALUES_INTERRUPTED' : ctypes.c_ulong(0x0000003D).value,
	'PICO_NOT_USED' : ctypes.c_ulong(0x0000003F).value,
	'PICO_INVALID_SAMPLERATIO' : ctypes.c_ulong(0x00000040).value,
	# Operation could not be carried out because device was in an invalid state.
	'PICO_INVALID_STATE' : ctypes.c_ulong(0x00000041).value,
	# Operation could not be carried out as rapid capture no of waveforms are greater than the
	# no of memory segments.
	'PICO_NOT_ENOUGH_SEGMENTS' : ctypes.c_ulong(0x00000042).value,
	# A driver function has already been called and not yet finished
	# only one call to the driver can be made at any one time
	'PICO_DRIVER_FUNCTION' : ctypes.c_ulong(0x00000043).value,
	'PICO_RESERVED' : ctypes.c_ulong(0x00000044).value,
	'PICO_INVALID_COUPLING' : ctypes.c_ulong(0x00000045).value,
	'PICO_BUFFERS_NOT_SET' : ctypes.c_ulong(0x00000046).value,
	'PICO_RATIO_MODE_NOT_SUPPORTED' : ctypes.c_ulong(0x00000047).value,
	'PICO_RAPID_NOT_SUPPORT_AGGREGATION' : ctypes.c_ulong(0x00000048).value,
	'PICO_INVALID_TRIGGER_PROPERTY' : ctypes.c_ulong(0x00000049).value,
	'PICO_INTERFACE_NOT_CONNECTED' : ctypes.c_ulong(0x0000004A).value,
	'PICO_RESISTANCE_AND_PROBE_NOT_ALLOWED' : ctypes.c_ulong(0x0000004B).value,
	'PICO_POWER_FAILED' : ctypes.c_ulong(0x0000004C).value,
	'PICO_SIGGEN_WAVEFORM_SETUP_FAILED' : ctypes.c_ulong(0x0000004D).value,
	'PICO_FPGA_FAIL' : ctypes.c_ulong(0x0000004E).value,
	'PICO_POWER_MANAGER' : ctypes.c_ulong(0x0000004F).value,
	'PICO_INVALID_ANALOGUE_OFFSET' : ctypes.c_ulong(0x00000050).value,
	# unable to configure the ps6000
	'PICO_PLL_LOCK_FAILED' : ctypes.c_ulong(0x00000051).value,
	# the ps6000 Analog board is not detectly connected
	#to the digital board
	'PICO_ANALOG_BOARD' : ctypes.c_ulong(0x00000052).value,
	# unable to configure the Signal Generator
	'PICO_CONFIG_FAIL_AWG' : ctypes.c_ulong(0x00000053).value,
	'PICO_INITIALISE_FPGA' : ctypes.c_ulong(0x00000054).value,
	'PICO_EXTERNAL_FREQUENCY_INVALID' : ctypes.c_ulong(0x00000056).value,
	'PICO_CLOCK_CHANGE_ERROR' : ctypes.c_ulong(0x00000057).value,
	'PICO_TRIGGER_AND_EXTERNAL_CLOCK_CLASH' : ctypes.c_ulong(0x00000058).value,
	'PICO_PWQ_AND_EXTERNAL_CLOCK_CLASH' : ctypes.c_ulong(0x00000059).value,
	'PICO_UNABLE_TO_OPEN_SCALING_FILE' : ctypes.c_ulong(0x0000005A).value,
	'PICO_MEMORY_CLOCK_FREQUENCY' : ctypes.c_ulong(0x0000005B).value,
	'PICO_I2C_NOT_RESPONDING' : ctypes.c_ulong(0x0000005C).value,
	'PICO_NO_CAPTURES_AVAILABLE' : ctypes.c_ulong(0x0000005D).value,
	'PICO_NOT_USED_IN_THIS_CAPTURE_MODE' : ctypes.c_ulong(0x0000005E).value,
	'PICO_GET_DATA_ACTIVE' : ctypes.c_ulong(0x00000103).value,
	# used by the PT104 (USB) when connected via the Network Socket
	'PICO_IP_NETWORKED' : ctypes.c_ulong(0x00000104).value,
	'PICO_INVALID_IP_ADDRESS' : ctypes.c_ulong(0x00000105).value,
	'PICO_IPSOCKET_FAILED' : ctypes.c_ulong(0x00000106).value,
	'PICO_IPSOCKET_TIMEDOUT' : ctypes.c_ulong(0x00000107).value,
	'PICO_SETTINGS_FAILED' : ctypes.c_ulong(0x00000108).value,
	'PICO_NETWORK_FAILED' : ctypes.c_ulong(0x00000109).value,
	'PICO_WS2_32_DLL_NOT_LOADED' : ctypes.c_ulong(0x0000010A).value,
	'PICO_INVALID_IP_PORT' : ctypes.c_ulong(0x0000010B).value,
	'PICO_COUPLING_NOT_SUPPORTED' : ctypes.c_ulong(0x0000010C).value,
	'PICO_BANDWIDTH_NOT_SUPPORTED' : ctypes.c_ulong(0x0000010D).value,
	'PICO_INVALID_BANDWIDTH' : ctypes.c_ulong(0x0000010E).value,
	'PICO_AWG_NOT_SUPPORTED' : ctypes.c_ulong(0x0000010F).value,
	'PICO_ETS_NOT_RUNNING' : ctypes.c_ulong(0x00000110).value,
	'PICO_SIG_GEN_WHITENOISE_NOT_SUPPORTED' : ctypes.c_ulong(0x00000111).value,
	'PICO_SIG_GEN_WAVETYPE_NOT_SUPPORTED' : ctypes.c_ulong(0x00000112).value,
	'PICO_INVALID_DIGITAL_PORT' : ctypes.c_ulong(0x00000113).value,
	'PICO_INVALID_DIGITAL_CHANNEL' : ctypes.c_ulong(0x00000114).value,
	'PICO_INVALID_DIGITAL_TRIGGER_DIRECTION' : ctypes.c_ulong(0x00000115).value,
	'PICO_SIG_GEN_PRBS_NOT_SUPPORTED' : ctypes.c_ulong(0x00000116).value,
	'PICO_ETS_NOT_AVAILABLE_WITH_LOGIC_CHANNELS' : ctypes.c_ulong(0x00000117).value,
	'PICO_WARNING_REPEAT_VALUE' : ctypes.c_ulong(0x00000118).value,
	'PICO_POWER_SUPPLY_CONNECTED' : ctypes.c_ulong(0x00000119).value,
	'PICO_POWER_SUPPLY_NOT_CONNECTED' : ctypes.c_ulong(0x0000011A).value,
	'PICO_POWER_SUPPLY_REQUEST_INVALID' : ctypes.c_ulong(0x0000011B).value,
	'PICO_POWER_SUPPLY_UNDERVOLTAGE' : ctypes.c_ulong(0x0000011C).value,
	'PICO_WATCHDOGTIMER' : ctypes.c_ulong(0x10000000).value,
    }