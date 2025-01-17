# Protocol Documentation


<a name="aquatroll-proto"></a>

## aquatroll.proto
Aquatroll

These messages are emitted by the In-Situ AquaTroll 500 probe.


<a name="blueye-protocol-AquaTrollParameterBlock"></a>

### AquaTrollParameterBlock
In-Situ Parameter Block

Up to NUMBER_OF_SENSOR_PARAMETERS blocks may be part of a sensor


| Field | Type | Description |
| ------| ---- | ----------- |
| measured_value | [ float](#float) |  |
| parameter_id | [ AquaTrollParameter](#blueye-protocol-AquaTrollParameter) |  |
| units_id | [ AquaTrollUnit](#blueye-protocol-AquaTrollUnit) |  |
| data_quality_ids | [repeated AquaTrollQuality](#blueye-protocol-AquaTrollQuality) |  |
| off_line_sentinel_value | [ float](#float) |  |
| available_units | [repeated AquaTrollUnit](#blueye-protocol-AquaTrollUnit) |  |

<a name="blueye-protocol-AquaTrollProbeMetadata"></a>

### AquaTrollProbeMetadata



| Field | Type | Description |
| ------| ---- | ----------- |
| timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| status | [ bool](#bool) |  |
| register_map_template_version | [ uint32](#uint32) |  |
| device_id | [ AquaTrollDevice](#blueye-protocol-AquaTrollDevice) |  |
| device_serial_number | [ uint32](#uint32) |  |
| manufacture_date | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| firmware_version | [ uint32](#uint32) |  |
| boot_code_version | [ uint32](#uint32) |  |
| hardware_version | [ uint32](#uint32) |  |
| max_data_logs | [ uint32](#uint32) |  |
| total_data_log_memory | [ uint32](#uint32) |  |
| total_battery_ticks | [ uint32](#uint32) |  |
| last_battery_change | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| device_name | [ string](#string) |  |
| site_name | [ string](#string) |  |
| latitude_coordinate | [ double](#double) |  |
| longitude_coordinate | [ double](#double) |  |
| altitude_coordinate | [ double](#double) |  |
| current_time_utc | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| device_status_flags | [repeated AquaTrollDeviceStatus](#blueye-protocol-AquaTrollDeviceStatus) |  |
| used_battery_ticks | [ uint32](#uint32) |  |
| used_data_log_memory | [ uint32](#uint32) |  |
| sensors | [repeated AquaTrollSensor](#blueye-protocol-AquaTrollSensor) |  |

<a name="blueye-protocol-AquaTrollSensorMetadata"></a>

### AquaTrollSensorMetadata
In-Situ AquaTroll 500 sensor metadata

(Mostly) static information about a connected sensor.

Refer to Section 7 Sensor Common Registers in the In-Situ Modbus
Communication Protocol


| Field | Type | Description |
| ------| ---- | ----------- |
| timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| sensor_id | [ AquaTrollSensor](#blueye-protocol-AquaTrollSensor) |  |
| sensor_serial_number | [ uint32](#uint32) |  |
| sensor_status_flags | [repeated AquaTrollSensorStatus](#blueye-protocol-AquaTrollSensorStatus) |  |
| last_factory_calibration | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| next_factory_calibration | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| last_user_calibration | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| next_user_calibration | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| warm_up_time_in_milliseconds | [ uint32](#uint32) |  |
| fast_sample_rate_in_milliseconds | [ uint32](#uint32) |  |
| number_of_sensor_parameters | [ uint32](#uint32) |  |
| alarm_and_warning_parameter_number | [ uint32](#uint32) |  |
| alarm_and_warning_enable_bits | [ uint32](#uint32) |  |
| high_alarm_set_value | [ float](#float) |  |
| high_alarm_clear_value | [ float](#float) |  |
| high_warning_set_value | [ float](#float) |  |
| high_warning_clear_value | [ float](#float) |  |
| low_warning_clear_value | [ float](#float) |  |
| low_warning_set_value | [ float](#float) |  |
| low_alarm_clear_value | [ float](#float) |  |
| low_alarm_set_value | [ float](#float) |  |
| parameter_blocks | [repeated AquaTrollParameterBlock](#blueye-protocol-AquaTrollParameterBlock) |  |

<a name="blueye-protocol-AquaTrollSensorMetadataArray"></a>

### AquaTrollSensorMetadataArray



| Field | Type | Description |
| ------| ---- | ----------- |
| timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| sensors | [repeated AquaTrollSensorMetadata](#blueye-protocol-AquaTrollSensorMetadata) |  |

<a name="blueye-protocol-AquaTrollSensorParameters"></a>

### AquaTrollSensorParameters



| Field | Type | Description |
| ------| ---- | ----------- |
| sensor_id | [ AquaTrollSensor](#blueye-protocol-AquaTrollSensor) |  |
| parameter_blocks | [repeated AquaTrollParameterBlock](#blueye-protocol-AquaTrollParameterBlock) |  |

<a name="blueye-protocol-AquaTrollSensorParametersArray"></a>

### AquaTrollSensorParametersArray



| Field | Type | Description |
| ------| ---- | ----------- |
| timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) |  |
| sensors | [repeated AquaTrollSensorParameters](#blueye-protocol-AquaTrollSensorParameters) |  |

<a name="blueye-protocol-SetAquaTrollConnectionStatus"></a>

### SetAquaTrollConnectionStatus
Request to change the In-Situ Aqua Troll connection status


| Field | Type | Description |
| ------| ---- | ----------- |
| connected | [ bool](#bool) | True to connect, false to disconnect |

<a name="blueye-protocol-SetAquaTrollParameterUnit"></a>

### SetAquaTrollParameterUnit
Request to set an In-Situ Aqua Troll parameter unit


| Field | Type | Description |
| ------| ---- | ----------- |
| sensor_id | [ AquaTrollSensor](#blueye-protocol-AquaTrollSensor) | Sensor id, f. ex. "SENSOR_CONDUCTIVITY_SENSOR" |
| parameter_id | [ AquaTrollParameter](#blueye-protocol-AquaTrollParameter) | Parameter name, f. ex. "PARAMETER_TEMPERATURE" |
| unit_id | [ AquaTrollUnit](#blueye-protocol-AquaTrollUnit) | Unit, f. ex. "UNIT_TEMP_CELSIUS" |



<a name="blueye-protocol-AquaTrollDevice"></a>

### AquaTrollDevice
Aqua Troll Device IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_DEVICE_UNSPECIFIED | 0 |  |
| AQUA_TROLL_DEVICE_LEVEL_TROLL_500 | 1 |  |
| AQUA_TROLL_DEVICE_LEVEL_TROLL_700 | 2 |  |
| AQUA_TROLL_DEVICE_BAROTROLL_500 | 3 |  |
| AQUA_TROLL_DEVICE_LEVEL_TROLL_300 | 4 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_200 | 5 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_600 | 7 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_100 | 10 |  |
| AQUA_TROLL_DEVICE_FLOW_TROLL_500 | 11 |  |
| AQUA_TROLL_DEVICE_RDO_PRO | 12 |  |
| AQUA_TROLL_DEVICE_RUGGED_TROLL_200 | 16 |  |
| AQUA_TROLL_DEVICE_RUGGED_BAROTROLL | 17 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_400 | 18 |  |
| AQUA_TROLL_DEVICE_RDO_TITAN | 19 |  |
| AQUA_TROLL_DEVICE_SMARTROLL | 21 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_600_VENTED | 26 |  |
| AQUA_TROLL_DEVICE_LEVEL_TROLL_400 | 30 |  |
| AQUA_TROLL_DEVICE_RDO_PRO_X | 31 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_500 | 33 |  |
| AQUA_TROLL_DEVICE_AQUA_TROLL_500_VENTED | 34 |  |



<a name="blueye-protocol-AquaTrollDeviceStatus"></a>

### AquaTrollDeviceStatus
Aqua Troll Device Status IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_HIGH_ALARM | 0 | protolint:disable:this ENUM_FIELD_NAMES_ZERO_VALUE_END_WITH |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_HIGH_WARNING | 1 |  |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_LOW_WARNING | 2 |  |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_LOW_ALARM | 3 |  |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_CALIBRATION_WARNING | 4 |  |
| AQUA_TROLL_DEVICE_STATUS_SENSOR_MALFUNCTION | 5 |  |
| AQUA_TROLL_DEVICE_STATUS_POWER_MANAGEMENT_DISABLED | 8 |  |
| AQUA_TROLL_DEVICE_STATUS_DEVICE_OFF_LINE | 9 |  |
| AQUA_TROLL_DEVICE_STATUS_DEVICE_HARDWARE_RESET_OCCURRED | 10 |  |
| AQUA_TROLL_DEVICE_STATUS_DEVICE_MALFUNCTION | 11 |  |
| AQUA_TROLL_DEVICE_STATUS_NO_EXTERNAL_POWER | 12 |  |
| AQUA_TROLL_DEVICE_STATUS_LOW_BATTERY | 13 |  |
| AQUA_TROLL_DEVICE_STATUS_LOW_MEMORY | 14 |  |



<a name="blueye-protocol-AquaTrollParameter"></a>

### AquaTrollParameter
Aqua Troll Parameter IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_PARAMETER_UNSPECIFIED | 0 |  |
| AQUA_TROLL_PARAMETER_TEMPERATURE | 1 |  |
| AQUA_TROLL_PARAMETER_PRESSURE | 2 |  |
| AQUA_TROLL_PARAMETER_DEPTH | 3 |  |
| AQUA_TROLL_PARAMETER_LEVEL_DEPTH_TO_WATER | 4 |  |
| AQUA_TROLL_PARAMETER_LEVEL_SURFACE_ELEVATION | 5 |  |
| AQUA_TROLL_PARAMETER_LATITUDE | 6 |  |
| AQUA_TROLL_PARAMETER_LONGITUDE | 7 |  |
| AQUA_TROLL_PARAMETER_ELEVATION | 8 |  |
| AQUA_TROLL_PARAMETER_ACTUAL_CONDUCTIVITY | 9 |  |
| AQUA_TROLL_PARAMETER_SPECIFIC_CONDUCTIVITY | 10 |  |
| AQUA_TROLL_PARAMETER_RESISTIVITY | 11 |  |
| AQUA_TROLL_PARAMETER_SALINITY | 12 |  |
| AQUA_TROLL_PARAMETER_TOTAL_DISSOLVED_SOLIDS | 13 |  |
| AQUA_TROLL_PARAMETER_DENSITY_OF_WATER | 14 |  |
| AQUA_TROLL_PARAMETER_SPECIFIC_GRAVITY | 15 |  |
| AQUA_TROLL_PARAMETER_BAROMETRIC_PRESSURE | 16 |  |
| AQUA_TROLL_PARAMETER_PH | 17 |  |
| AQUA_TROLL_PARAMETER_PH_MV | 18 |  |
| AQUA_TROLL_PARAMETER_ORP | 19 |  |
| AQUA_TROLL_PARAMETER_DISSOLVED_OXYGEN_CONCENTRATION | 20 |  |
| AQUA_TROLL_PARAMETER_DISSOLVED_OXYGEN_SATURATION | 21 |  |
| AQUA_TROLL_PARAMETER_NITRATE | 22 |  |
| AQUA_TROLL_PARAMETER_AMMONIUM | 23 |  |
| AQUA_TROLL_PARAMETER_CHLORIDE | 24 |  |
| AQUA_TROLL_PARAMETER_TURBIDITY | 25 |  |
| AQUA_TROLL_PARAMETER_BATTERY_VOLTAGE | 26 |  |
| AQUA_TROLL_PARAMETER_HEAD | 27 |  |
| AQUA_TROLL_PARAMETER_FLOW | 28 |  |
| AQUA_TROLL_PARAMETER_TOTAL_FLOW | 29 |  |
| AQUA_TROLL_PARAMETER_OXYGEN_PARTIAL_PRESSURE | 30 |  |
| AQUA_TROLL_PARAMETER_TOTAL_SUSPENDED_SOLIDS | 31 |  |
| AQUA_TROLL_PARAMETER_EXTERNAL_VOLTAGE | 32 |  |
| AQUA_TROLL_PARAMETER_BATTERY_CAPACITY_REMAINING | 33 |  |
| AQUA_TROLL_PARAMETER_RHODAMINE_WT_CONCENTRATION | 34 |  |
| AQUA_TROLL_PARAMETER_RHODAMINE_WT_FLUORESCENCE_INTENSITY | 35 |  |
| AQUA_TROLL_PARAMETER_CHLORIDE_CL_MV | 36 |  |
| AQUA_TROLL_PARAMETER_NITRATE_AS_NITROGEN_NO3_N_CONCENTRATION | 37 |  |
| AQUA_TROLL_PARAMETER_NITRATE_NO3_MV | 38 |  |
| AQUA_TROLL_PARAMETER_AMMONIUM_AS_NITROGEN_NH4_PLUS_N_CONCENTRATION | 39 |  |
| AQUA_TROLL_PARAMETER_AMMONIUM_NH4_MV | 40 |  |
| AQUA_TROLL_PARAMETER_AMMONIA_AS_NITROGEN_NH3_N_CONCENTRATION | 41 |  |
| AQUA_TROLL_PARAMETER_TOTAL_AMMONIA_AS_NITROGEN_NH3_N_CONCENTRATION | 42 |  |
| AQUA_TROLL_PARAMETER_EH | 48 |  |
| AQUA_TROLL_PARAMETER_VELOCITY | 49 |  |
| AQUA_TROLL_PARAMETER_CHLOROPHYLL_A_CONCENTRATION | 50 |  |
| AQUA_TROLL_PARAMETER_CHLOROPHYLL_A_FLUORESCENCE_INTENSITY | 51 |  |
| AQUA_TROLL_PARAMETER_BLUE_GREEN_ALGAE_PHYCOCYANIN_CONCENTRATION | 54 |  |
| AQUA_TROLL_PARAMETER_BLUE_GREEN_ALGAE_PHYCOCYANIN_FLUORESCENCE_INTENSITY | 55 |  |
| AQUA_TROLL_PARAMETER_BLUE_GREEN_ALGAE_PHYCOERYTHRIN_CONCENTRATION | 58 |  |
| AQUA_TROLL_PARAMETER_BLUE_GREEN_ALGAE_PHYCOERYTHRIN_FLUORESCENCE_INTENSITY | 59 |  |
| AQUA_TROLL_PARAMETER_FLUORESCEIN_WT_CONCENTRATION | 67 |  |
| AQUA_TROLL_PARAMETER_FLUORESCEIN_WT_FLUORESCENCE_INTENSITY | 68 |  |
| AQUA_TROLL_PARAMETER_FLUORESCENT_DISSOLVED_ORGANIC_MATTER_CONCENTRATION | 69 |  |
| AQUA_TROLL_PARAMETER_FLUORESCENT_DISSOLVED_ORGANIC_MATTER_FLUORESCENCE_INTENSITY | 70 |  |
| AQUA_TROLL_PARAMETER_CRUDE_OIL_CONCENTRATION | 80 |  |
| AQUA_TROLL_PARAMETER_CRUDE_OIL_FLUORESCENCE_INTENSITY | 81 |  |
| AQUA_TROLL_PARAMETER_COLORED_DISSOLVED_ORGANIC_MATTER_CONCENTRATION | 87 |  |



<a name="blueye-protocol-AquaTrollQuality"></a>

### AquaTrollQuality
Aqua Troll Quality IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_QUALITY_NORMAL | 0 | protolint:disable:this ENUM_FIELD_NAMES_ZERO_VALUE_END_WITH |
| AQUA_TROLL_QUALITY_USER_CAL_EXPIRED | 1 |  |
| AQUA_TROLL_QUALITY_FACTORY_CAL_EXPIRED | 2 |  |
| AQUA_TROLL_QUALITY_ERROR | 3 |  |
| AQUA_TROLL_QUALITY_WARM_UP | 4 |  |
| AQUA_TROLL_QUALITY_SENSOR_WARNING | 5 |  |
| AQUA_TROLL_QUALITY_CALIBRATING | 6 |  |
| AQUA_TROLL_QUALITY_OFF_LINE | 7 |  |



<a name="blueye-protocol-AquaTrollSensor"></a>

### AquaTrollSensor
Aqua Troll Sensor IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_SENSOR_UNSPECIFIED | 0 |  |
| AQUA_TROLL_SENSOR_TEMPERATURE | 1 |  |
| AQUA_TROLL_SENSOR_S5_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 2 |  |
| AQUA_TROLL_SENSOR_S15_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 3 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 4 |  |
| AQUA_TROLL_SENSOR_S100_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 5 |  |
| AQUA_TROLL_SENSOR_S300_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 6 |  |
| AQUA_TROLL_SENSOR_S500_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 7 |  |
| AQUA_TROLL_SENSOR_S1000_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 8 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 9 |  |
| AQUA_TROLL_SENSOR_S100_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 10 |  |
| AQUA_TROLL_SENSOR_S300_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 11 |  |
| AQUA_TROLL_SENSOR_S500_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_AND_TEMPERATURE | 12 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_TEMPERATURE | 13 |  |
| AQUA_TROLL_SENSOR_S5_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 14 |  |
| AQUA_TROLL_SENSOR_S15_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 15 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 16 |  |
| AQUA_TROLL_SENSOR_S100_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 17 |  |
| AQUA_TROLL_SENSOR_S300_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 18 |  |
| AQUA_TROLL_SENSOR_S500_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 19 |  |
| AQUA_TROLL_SENSOR_NOT_USED | 20 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 21 |  |
| AQUA_TROLL_SENSOR_S100_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 22 |  |
| AQUA_TROLL_SENSOR_S300_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 23 |  |
| AQUA_TROLL_SENSOR_S500_PSI_FULL_SCALE_ABSOLUTE_PRESSURE_WITH_LEVEL_TEMPERATURE_AND_CONDUCTIVITY | 24 |  |
| AQUA_TROLL_SENSOR_S165_PSI_FULL_SCALE_ABSOLUTE_PRESSURE | 25 |  |
| AQUA_TROLL_SENSOR_PH_ANALOG_SENSOR | 26 |  |
| AQUA_TROLL_SENSOR_PH_ORP_ANALOG_SENSOR | 27 |  |
| AQUA_TROLL_SENSOR_DISSOLVED_OXYGEN_CLARK_CELL_ANALOG_SENSOR | 28 |  |
| AQUA_TROLL_SENSOR_NITRATE_ANALOG_SENSOR | 29 |  |
| AQUA_TROLL_SENSOR_AMMONIUM_ANALOG_SENSOR | 30 |  |
| AQUA_TROLL_SENSOR_CHLORIDE_ANALOG_SENSOR | 31 |  |
| AQUA_TROLL_SENSOR_S100_FOOT_FULL_SCALE_LEVEL_WITH_ABSOLUTE_PRESSURE_AND_TEMPERATURE | 32 |  |
| AQUA_TROLL_SENSOR_S250_FOOT_FULL_SCALE_LEVEL_WITH_ABSOLUTE_PRESSURE_AND_TEMPERATURE | 33 |  |
| AQUA_TROLL_SENSOR_S30_FOOT_FULL_SCALE_LEVEL_WITH_ABSOLUTE_PRESSURE_AND_TEMPERATURE | 34 |  |
| AQUA_TROLL_SENSOR_CONDUCTIVITY_AND_TEMPERATURE | 35 |  |
| AQUA_TROLL_SENSOR_S5_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 36 |  |
| AQUA_TROLL_SENSOR_S15_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 37 |  |
| AQUA_TROLL_SENSOR_S30_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 38 |  |
| AQUA_TROLL_SENSOR_S100_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 39 |  |
| AQUA_TROLL_SENSOR_S300_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 40 |  |
| AQUA_TROLL_SENSOR_S500_PSI_FULL_SCALE_GAUGE_PRESSURE_WITH_TEMPERATURE_HEAD_AND_FLOW | 41 |  |
| AQUA_TROLL_SENSOR_OPTICAL_DISSOLVED_OXYGEN_WITH_TEMPERATURE | 42 |  |
| AQUA_TROLL_SENSOR_S1_BAR | 43 |  |
| AQUA_TROLL_SENSOR_S2_BAR | 44 |  |
| AQUA_TROLL_SENSOR_S5_BAR | 45 |  |
| AQUA_TROLL_SENSOR_TURBIDITY_SENSOR | 50 |  |
| AQUA_TROLL_SENSOR_TEMPERATURE_SENSOR | 55 |  |
| AQUA_TROLL_SENSOR_CONDUCTIVITY_SENSOR | 56 |  |
| AQUA_TROLL_SENSOR_RDO_SENSOR | 57 |  |
| AQUA_TROLL_SENSOR_PH_ORP_SENSOR | 58 |  |
| AQUA_TROLL_SENSOR_RHODAMINE_WT_SENSOR | 60 |  |
| AQUA_TROLL_SENSOR_CHLOROPHYLL_A_SENSOR | 62 |  |
| AQUA_TROLL_SENSOR_BLUE_GREEN_ALGAE_PHYCOCYANIN_SENSOR | 64 |  |
| AQUA_TROLL_SENSOR_BLUE_GREEN_ALGAE_PHYCOERYTHRIN_SENSOR | 65 |  |
| AQUA_TROLL_SENSOR_NITRATE_ISE_SENSOR | 70 |  |
| AQUA_TROLL_SENSOR_AMMONIUM_ISE_SENSOR | 71 |  |
| AQUA_TROLL_SENSOR_CHLORIDE_ISE_SENSOR | 72 |  |
| AQUA_TROLL_SENSOR_PROBE_PARAMETERS | 79 |  |



<a name="blueye-protocol-AquaTrollSensorStatus"></a>

### AquaTrollSensorStatus
Aqua Troll Sensor Status IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_HIGH_ALARM | 0 | protolint:disable:this ENUM_FIELD_NAMES_ZERO_VALUE_END_WITH |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_HIGH_WARNING | 1 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_LOW_WARNING | 2 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_LOW_ALARM | 3 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_CALIBRATION_WARNING | 4 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_MALFUNCTION | 5 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_MODE_BIT_1 | 8 |  |
| AQUA_TROLL_SENSOR_STATUS_SENSOR_MODE_BIT_2 | 9 |  |



<a name="blueye-protocol-AquaTrollUnit"></a>

### AquaTrollUnit
Aqua Troll Unit IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| AQUA_TROLL_UNIT_UNSPECIFIED | 0 |  |
| AQUA_TROLL_UNIT_TEMP_CELSIUS | 1 |  |
| AQUA_TROLL_UNIT_TEMP_FARENHEIT | 2 |  |
| AQUA_TROLL_UNIT_TEMP_KELVIN | 3 |  |
| AQUA_TROLL_UNIT_POUNDS_PER_SQUARE_INCH | 17 |  |
| AQUA_TROLL_UNIT_PASCALS | 18 |  |
| AQUA_TROLL_UNIT_KILOPASCALS | 19 |  |
| AQUA_TROLL_UNIT_BARS | 20 |  |
| AQUA_TROLL_UNIT_MILLIBARS | 21 |  |
| AQUA_TROLL_UNIT_MILLIMETERS_OF_MERCURY | 22 |  |
| AQUA_TROLL_UNIT_INCHES_OF_MERCURY | 23 |  |
| AQUA_TROLL_UNIT_CENTIMETERS_OF_WATER | 24 |  |
| AQUA_TROLL_UNIT_INCHES_OF_WATER | 25 |  |
| AQUA_TROLL_UNIT_TORR | 26 |  |
| AQUA_TROLL_UNIT_STANDARD_ATMOSPHERE | 27 |  |
| AQUA_TROLL_UNIT_MILLIMETERS | 33 |  |
| AQUA_TROLL_UNIT_CENTIMETERS | 34 |  |
| AQUA_TROLL_UNIT_METERS | 35 |  |
| AQUA_TROLL_UNIT_KILOMETER | 36 |  |
| AQUA_TROLL_UNIT_INCHES | 37 |  |
| AQUA_TROLL_UNIT_FEET | 38 |  |
| AQUA_TROLL_UNIT_DEGREES | 49 |  |
| AQUA_TROLL_UNIT_MINUTES | 50 |  |
| AQUA_TROLL_UNIT_SECONDS | 51 |  |
| AQUA_TROLL_UNIT_MICROSIEMENS_PER_CENTIMETER | 65 |  |
| AQUA_TROLL_UNIT_MILLISIEMENS_PER_CENTIMETER | 66 |  |
| AQUA_TROLL_UNIT_OHM_CENTIMETERS | 81 |  |
| AQUA_TROLL_UNIT_PRACTICAL_SALINITY_UNITS | 97 |  |
| AQUA_TROLL_UNIT_PARTS_PER_THOUSAND_SALINITY | 98 |  |
| AQUA_TROLL_UNIT_PARTS_PER_MILLION | 113 |  |
| AQUA_TROLL_UNIT_PARTS_PER_THOUSAND | 114 |  |
| AQUA_TROLL_UNIT_PARTS_PER_MILLION_NITROGEN | 115 |  |
| AQUA_TROLL_UNIT_PARTS_PER_MILLION_CHLORIDE | 116 |  |
| AQUA_TROLL_UNIT_MILLIGRAMS_PER_LITER | 117 |  |
| AQUA_TROLL_UNIT_MICROGRAMS_PER_LITER | 118 |  |
| AQUA_TROLL_UNIT_MICROMOLES_PER_LITER_DEPRECATED | 119 |  |
| AQUA_TROLL_UNIT_GRAMS_PER_LITER | 120 |  |
| AQUA_TROLL_UNIT_PARTS_PER_BILLION | 121 |  |
| AQUA_TROLL_UNIT_GRAMS_PER_CUBIC_CENTIMETER | 129 |  |
| AQUA_TROLL_UNIT_PH | 145 |  |
| AQUA_TROLL_UNIT_MICRO_VOLTS | 161 |  |
| AQUA_TROLL_UNIT_MILLI_VOLTS | 162 |  |
| AQUA_TROLL_UNIT_VOLTS | 163 |  |
| AQUA_TROLL_UNIT_PERCENT_SATURATION | 177 |  |
| AQUA_TROLL_UNIT_FORMAZIN_NEPHELOMETRIC_UNITS | 193 |  |
| AQUA_TROLL_UNIT_NEPHELOMETRIC_TURBIDITY_UNITS | 194 |  |
| AQUA_TROLL_UNIT_FORMAZIN_TURBIDITY_UNITS | 195 |  |
| AQUA_TROLL_UNIT_CUBIC_FEET_PER_SECOND | 209 |  |
| AQUA_TROLL_UNIT_CUBIC_FEET_PER_MINUTE | 210 |  |
| AQUA_TROLL_UNIT_CUBIC_FEET_PER_HOUR | 211 |  |
| AQUA_TROLL_UNIT_CUBIC_FEET_PER_DAY | 212 |  |
| AQUA_TROLL_UNIT_GALLONS_PER_SECOND | 213 |  |
| AQUA_TROLL_UNIT_GALLONS_PER_MINUTE | 214 |  |
| AQUA_TROLL_UNIT_GALLONS_PER_HOUR | 215 |  |
| AQUA_TROLL_UNIT_MILLIONS_OF_GALLONS_PER_DAY | 216 |  |
| AQUA_TROLL_UNIT_CUBIC_METERS_PER_SECOND | 217 |  |
| AQUA_TROLL_UNIT_CUBIC_METERS_PER_MINUTE | 218 |  |
| AQUA_TROLL_UNIT_CUBIC_METERS_PER_HOUR | 219 |  |
| AQUA_TROLL_UNIT_CUBIC_METERS_PER_DAY | 220 |  |
| AQUA_TROLL_UNIT_LITERS_PER_SECOND | 221 |  |
| AQUA_TROLL_UNIT_MILLIONS_OF_LITERS_PER_DAY | 222 |  |
| AQUA_TROLL_UNIT_MILLILITERS_PER_MINUTE | 223 |  |
| AQUA_TROLL_UNIT_THOUSANDS_OF_LITERS_PER_DAY | 224 |  |
| AQUA_TROLL_UNIT_CUBIC_FEET | 225 |  |
| AQUA_TROLL_UNIT_GALLONS | 226 |  |
| AQUA_TROLL_UNIT_MILLIONS_OF_GALLONS | 227 |  |
| AQUA_TROLL_UNIT_CUBIC_METERS | 228 |  |
| AQUA_TROLL_UNIT_LITERS | 229 |  |
| AQUA_TROLL_UNIT_ACRE_FEET | 230 |  |
| AQUA_TROLL_UNIT_MILLILITERS | 231 |  |
| AQUA_TROLL_UNIT_MILLIONS_OF_LITERS | 232 |  |
| AQUA_TROLL_UNIT_THOUSANDS_OF_LITERS | 233 |  |
| AQUA_TROLL_UNIT_ACRE_INCHES | 234 |  |
| AQUA_TROLL_UNIT_PERCENT | 241 |  |
| AQUA_TROLL_UNIT_RELATIVE_FLUORESCENCE_UNITS | 257 |  |
| AQUA_TROLL_UNIT_MILLILITERS_PER_SECOND | 273 |  |
| AQUA_TROLL_UNIT_MILLILITERS_PER_HOUR | 274 |  |
| AQUA_TROLL_UNIT_LITERS_PER_MINUTE | 275 |  |
| AQUA_TROLL_UNIT_LITERS_PER_HOUR | 276 |  |
| AQUA_TROLL_UNIT_MICROAMPS | 289 |  |
| AQUA_TROLL_UNIT_MILLIAMPS | 290 |  |
| AQUA_TROLL_UNIT_AMPS | 291 |  |
| AQUA_TROLL_UNIT_FEET_PER_SECOND | 305 |  |
| AQUA_TROLL_UNIT_METERS_PER_SECOND | 306 |  |



<a name="blueye-protocol-Type"></a>

### Type
Type IDs

| Name | Number | Description |
| ---- | ------ | ----------- |
| TYPE_UNSPECIFIED | 0 |  |
| TYPE_SHORT | 1 |  |
| TYPE_UNSIGNED_SHORT | 2 |  |
| TYPE_LONG | 3 |  |
| TYPE_UNSIGNED_LONG | 4 |  |
| TYPE_FLOAT | 5 |  |
| TYPE_DOUBLE | 6 |  |
| TYPE_CHARACTER | 7 |  |
| TYPE_STRING | 8 |  |
| TYPE_TIME | 9 |  |




<a name="control-proto"></a>

## control.proto
Control

These messages define control messages accepted by the Blueye drone.


<a name="blueye-protocol-ActivateGuestPortsCtrl"></a>

### ActivateGuestPortsCtrl
Activated the guest port power


<a name="blueye-protocol-ActivateMultibeamCtrl"></a>

### ActivateMultibeamCtrl
Activate multibeam


| Field | Type | Description |
| ------| ---- | ----------- |
| config | [ MultibeamConfig](#blueye-protocol-MultibeamConfig) | Message with the multibeam ping configuration to set on connect |

<a name="blueye-protocol-AutoAltitudeCtrl"></a>

### AutoAltitudeCtrl
Issue a command to set auto altitude to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ AutoAltitudeState](#blueye-protocol-AutoAltitudeState) | State of the altitude controller |

<a name="blueye-protocol-AutoDepthCtrl"></a>

### AutoDepthCtrl
Issue a command to set auto depth to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ AutoDepthState](#blueye-protocol-AutoDepthState) | State of the depth controller |

<a name="blueye-protocol-AutoHeadingCtrl"></a>

### AutoHeadingCtrl
Issue a command to set auto heading to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ AutoHeadingState](#blueye-protocol-AutoHeadingState) | State of the heading controller |

<a name="blueye-protocol-AutoPilotHeaveCtrl"></a>

### AutoPilotHeaveCtrl
Issue a command to set Auto Pilot for vertiacl movement to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ AutoPilotHeaveState](#blueye-protocol-AutoPilotHeaveState) | State of the auto pilot heave controller |

<a name="blueye-protocol-AutoPilotSurgeYawCtrl"></a>

### AutoPilotSurgeYawCtrl
Issue a command to set Auto Pilot for cruising and turning to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ AutoPilotSurgeYawState](#blueye-protocol-AutoPilotSurgeYawState) | State of the auto pilot surge yaw controller |

<a name="blueye-protocol-CalibrateDvlGyroCtrl"></a>

### CalibrateDvlGyroCtrl
Issue a command to calibrate the DVL gyro.


<a name="blueye-protocol-CancelCalibrationCtrl"></a>

### CancelCalibrationCtrl
Issue a command to cancel compass calibration.


<a name="blueye-protocol-ClearMissionCtrl"></a>

### ClearMissionCtrl
Clear the loaded mission.


<a name="blueye-protocol-DeactivateGuestPortsCtrl"></a>

### DeactivateGuestPortsCtrl
Deactivate the guest port power


<a name="blueye-protocol-DeactivateMultibeamCtrl"></a>

### DeactivateMultibeamCtrl
Deactivate multibeam


<a name="blueye-protocol-EndDiveCtrl"></a>

### EndDiveCtrl
Message sent when the user hits the end dive button in the app.

The message does not do anything, but is included in the log files so we can see
at which point the user exited the dive view.


<a name="blueye-protocol-FinishCalibrationCtrl"></a>

### FinishCalibrationCtrl
Issue a command to finish compass calibration.


<a name="blueye-protocol-GenericServoCtrl"></a>

### GenericServoCtrl
Issue a command to set a generic servo value.


| Field | Type | Description |
| ------| ---- | ----------- |
| servo | [ GenericServo](#blueye-protocol-GenericServo) | Message with the desired servo value. |

<a name="blueye-protocol-GripperCtrl"></a>

### GripperCtrl
Issue a command to control the gripper.


| Field | Type | Description |
| ------| ---- | ----------- |
| gripper_velocities | [ GripperVelocities](#blueye-protocol-GripperVelocities) | The desired gripping and rotation velocity. |

<a name="blueye-protocol-GuestportLightsCtrl"></a>

### GuestportLightsCtrl
Issue a command to set the guest port light intensity.


| Field | Type | Description |
| ------| ---- | ----------- |
| lights | [ Lights](#blueye-protocol-Lights) | Message with the desired light intensity. |

<a name="blueye-protocol-LaserCtrl"></a>

### LaserCtrl
Issue a command to set the laser intensity.


| Field | Type | Description |
| ------| ---- | ----------- |
| laser | [ Laser](#blueye-protocol-Laser) | Message with the desired laser intensity. |

<a name="blueye-protocol-LightsCtrl"></a>

### LightsCtrl
Issue a command to set the main light intensity.


| Field | Type | Description |
| ------| ---- | ----------- |
| lights | [ Lights](#blueye-protocol-Lights) | Message with the desired light intensity. |

<a name="blueye-protocol-MotionInputCtrl"></a>

### MotionInputCtrl
Issue a command to move the drone in the surge, sway, heave, or yaw direction.


| Field | Type | Description |
| ------| ---- | ----------- |
| motion_input | [ MotionInput](#blueye-protocol-MotionInput) | Message with the desired movement in each direction. |

<a name="blueye-protocol-MultibeamServoCtrl"></a>

### MultibeamServoCtrl
Issue a command to set multibeam servo angle.


| Field | Type | Description |
| ------| ---- | ----------- |
| servo | [ MultibeamServo](#blueye-protocol-MultibeamServo) | Message with the desired servo angle. |

<a name="blueye-protocol-PauseMissionCtrl"></a>

### PauseMissionCtrl
Issue a command to pause the loaded mission.


<a name="blueye-protocol-PilotGPSPositionCtrl"></a>

### PilotGPSPositionCtrl
Issue a command with the GPS position of the pilot.


| Field | Type | Description |
| ------| ---- | ----------- |
| position | [ LatLongPosition](#blueye-protocol-LatLongPosition) | The GPS position of the pilot. |

<a name="blueye-protocol-PingerConfigurationCtrl"></a>

### PingerConfigurationCtrl
Issue a command to set the pinger configuration.


| Field | Type | Description |
| ------| ---- | ----------- |
| configuration | [ PingerConfiguration](#blueye-protocol-PingerConfiguration) | Message with the pinger configuration to set. |

<a name="blueye-protocol-RecordCtrl"></a>

### RecordCtrl
Issue a command to start video recording.


| Field | Type | Description |
| ------| ---- | ----------- |
| record_on | [ RecordOn](#blueye-protocol-RecordOn) | Message specifying which cameras to record. |

<a name="blueye-protocol-ResetOdometerCtrl"></a>

### ResetOdometerCtrl
Issue a command to reset the odometer.


<a name="blueye-protocol-ResetPositionCtrl"></a>

### ResetPositionCtrl
Issue a command to reset the position estimate.


| Field | Type | Description |
| ------| ---- | ----------- |
| settings | [ ResetPositionSettings](#blueye-protocol-ResetPositionSettings) | Reset settings. |

<a name="blueye-protocol-RestartGuestPortsCtrl"></a>

### RestartGuestPortsCtrl
Restart the guest ports by turning power on and off


| Field | Type | Description |
| ------| ---- | ----------- |
| restart_info | [ GuestPortRestartInfo](#blueye-protocol-GuestPortRestartInfo) | Message with information about how long to keep the guest ports off. |

<a name="blueye-protocol-RunMissionCtrl"></a>

### RunMissionCtrl
Issue a command to start and pause the loaded mission.


<a name="blueye-protocol-SetAquaTrollConnectionStatusCtrl"></a>

### SetAquaTrollConnectionStatusCtrl
Request to change the In-Situ Aqua Troll connection status


| Field | Type | Description |
| ------| ---- | ----------- |
| connection_status | [ SetAquaTrollConnectionStatus](#blueye-protocol-SetAquaTrollConnectionStatus) | Message with information about which parameter to set and the unit to set it to. |

<a name="blueye-protocol-SetAquaTrollParameterUnitCtrl"></a>

### SetAquaTrollParameterUnitCtrl
Request to set an In-Situ Aqua Troll parameter unit


| Field | Type | Description |
| ------| ---- | ----------- |
| parameter_info | [ SetAquaTrollParameterUnit](#blueye-protocol-SetAquaTrollParameterUnit) | Message with information about which parameter to set and the unit to set it to. |

<a name="blueye-protocol-SetMultibeamConfigCtrl"></a>

### SetMultibeamConfigCtrl
Update multibeam settings


| Field | Type | Description |
| ------| ---- | ----------- |
| config | [ MultibeamConfig](#blueye-protocol-MultibeamConfig) | Message with the multibeam ping configuration to set. |

<a name="blueye-protocol-StartCalibrationCtrl"></a>

### StartCalibrationCtrl
Issue a command to start compass calibration.


<a name="blueye-protocol-StartDiveCtrl"></a>

### StartDiveCtrl
Message sent when the user hits the start dive button in the app.

The message does not do anything, but is included in the log files so we can see
at which point the user entered the dive view.


<a name="blueye-protocol-StationKeepingCtrl"></a>

### StationKeepingCtrl
Issue a command to set station keeping to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ StationKeepingState](#blueye-protocol-StationKeepingState) | State of the station keeping controller |

<a name="blueye-protocol-SystemTimeCtrl"></a>

### SystemTimeCtrl
Issue a command to set the system time on the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| system_time | [ SystemTime](#blueye-protocol-SystemTime) | Message with the system time to set. |

<a name="blueye-protocol-TakePictureCtrl"></a>

### TakePictureCtrl
Issue a command to take a picture.


<a name="blueye-protocol-TiltStabilizationCtrl"></a>

### TiltStabilizationCtrl
Issue a command to enable or disable tilt stabilization.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ TiltStabilizationState](#blueye-protocol-TiltStabilizationState) | Message with the tilt stabilization state to set. |

<a name="blueye-protocol-TiltVelocityCtrl"></a>

### TiltVelocityCtrl
Issue a command to tilt the drone camera.


| Field | Type | Description |
| ------| ---- | ----------- |
| velocity | [ TiltVelocity](#blueye-protocol-TiltVelocity) | Message with the desired tilt velocity (direction and speed). |

<a name="blueye-protocol-WatchdogCtrl"></a>

### WatchdogCtrl
Issue a watchdog message to indicate that the remote client is connected and working as expected.

If a watchdog message is not received every second, the drone will turn off lights and other auto
functions to indicate that connection with the client has been lost.


| Field | Type | Description |
| ------| ---- | ----------- |
| connection_duration | [ ConnectionDuration](#blueye-protocol-ConnectionDuration) | Message with the number of seconds the client has been connected. |
| client_id | [ uint32](#uint32) | The ID of the client, received in the ConnectClientRep response. |

<a name="blueye-protocol-WaterDensityCtrl"></a>

### WaterDensityCtrl
Issue a command to set the water density.


| Field | Type | Description |
| ------| ---- | ----------- |
| density | [ WaterDensity](#blueye-protocol-WaterDensity) | Message with the water density to set. |

<a name="blueye-protocol-WeatherVaningCtrl"></a>

### WeatherVaningCtrl
Issue a command to set station keeping with weather vaning to a desired state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ WeatherVaningState](#blueye-protocol-WeatherVaningState) | State of the weather vaning controller |




<a name="message_formats-proto"></a>

## message_formats.proto
Common messages

These are used for logging as well as building requests and responses.


<a name="blueye-protocol-Altitude"></a>

### Altitude
Drone altitude over seabed, typically obtained from a DVL.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Drone altitude over seabed (m) |
| is_valid | [ bool](#bool) | If altitude is valid or not |

<a name="blueye-protocol-Attitude"></a>

### Attitude
The attitude of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| roll | [ float](#float) | Roll angle (-180°..180°) |
| pitch | [ float](#float) | Pitch angle (-180°..180°) |
| yaw | [ float](#float) | Yaw angle (-180°..180°) |

<a name="blueye-protocol-AutoAltitudeState"></a>

### AutoAltitudeState
Auto altitude state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If auto altitude is enabled |

<a name="blueye-protocol-AutoDepthState"></a>

### AutoDepthState
Auto depth state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If auto depth is enabled |

<a name="blueye-protocol-AutoHeadingState"></a>

### AutoHeadingState
Auto heading state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If auto heading is enabled |

<a name="blueye-protocol-AutoPilotHeaveState"></a>

### AutoPilotHeaveState
Auto pilot heave state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If auto pilot heave is enabled |

<a name="blueye-protocol-AutoPilotSurgeYawState"></a>

### AutoPilotSurgeYawState
Auto pilot surge yaw state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If auto pilot surge yaw is enabled |

<a name="blueye-protocol-Battery"></a>

### Battery
Essential battery information.


| Field | Type | Description |
| ------| ---- | ----------- |
| voltage | [ float](#float) | Battery voltage (V) |
| level | [ float](#float) | Battery level (0..1) |
| temperature | [ float](#float) | Battery temperature (°C) |

<a name="blueye-protocol-BatteryBQ40Z50"></a>

### BatteryBQ40Z50
Battery information message.

Detailed information about all aspects of the connected Blueye Smart Battery,
using the BQ40Z50 BMS.


| Field | Type | Description |
| ------| ---- | ----------- |
| voltage | [ BatteryBQ40Z50.Voltage](#blueye-protocol-BatteryBQ40Z50-Voltage) | Voltage of the battery cells |
| temperature | [ BatteryBQ40Z50.Temperature](#blueye-protocol-BatteryBQ40Z50-Temperature) | Temperature of the battery cells |
| status | [ BatteryBQ40Z50.BatteryStatus](#blueye-protocol-BatteryBQ40Z50-BatteryStatus) | Battery status flags |
| current | [ float](#float) | Measured current from the coulomb counter (A) |
| average_current | [ float](#float) | Average current (A) |
| relative_state_of_charge | [ float](#float) | Predicted remaining battery capacity as a factor of full_charge_capacity (0..1) |
| absolute_state_of_charge | [ float](#float) | Predicted remaining battery capacity (0..1) |
| calculated_state_of_charge | [ float](#float) | Calculated state of charge (0..1) |
| remaining_capacity | [ float](#float) | Predicted remaining battery capacity (Ah) |
| full_charge_capacity | [ float](#float) | Predicted battery capacity when fully charged (Ah) |
| runtime_to_empty | [ uint32](#uint32) | Predicted remaining battery capacity based on the present rate of discharge (s) |
| average_time_to_empty | [ uint32](#uint32) | Predicted remaining battery capacity based on average_current (s) |
| average_time_to_full | [ uint32](#uint32) | Predicted time-to-full charge based on average_current (s) |
| charging_current | [ float](#float) | Desired charging current (A) |
| charging_voltage | [ float](#float) | Desired charging voltage (V) |
| cycle_count | [ uint32](#uint32) | Number of charging cycles |
| design_capacity | [ float](#float) | Design capacity (Ah) |
| manufacture_date | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Manufacture date |
| serial_number | [ uint32](#uint32) | Serial number |
| manufacturer_name | [ string](#string) | Manufacturer name |
| device_name | [ string](#string) | Device name |
| device_chemistry | [ string](#string) | Battery chemistry |
| lifetimes | [ BatteryBQ40Z50.BatteryLifetimes](#blueye-protocol-BatteryBQ40Z50-BatteryLifetimes) | Battery lifetimes |
| safety_events | [ BatteryBQ40Z50.BatterySafetyEvents](#blueye-protocol-BatteryBQ40Z50-BatterySafetyEvents) | Battery safety events |
| charging_events | [ BatteryBQ40Z50.BatteryChargingEvents](#blueye-protocol-BatteryBQ40Z50-BatteryChargingEvents) | Battery charging events |

<a name="blueye-protocol-BatteryBQ40Z50-BatteryChargingEvents"></a>

### BatteryBQ40Z50.BatteryChargingEvents



| Field | Type | Description |
| ------| ---- | ----------- |
| charge_termination_events_count | [ uint32](#uint32) | Total number of valid charge termination events (events) |
| charge_termination_last_event | [ uint32](#uint32) | Last valid charge termination in cycle count cycles (cycles) |

<a name="blueye-protocol-BatteryBQ40Z50-BatteryLifetimes"></a>

### BatteryBQ40Z50.BatteryLifetimes



| Field | Type | Description |
| ------| ---- | ----------- |
| max_cell_voltages | [ BatteryBQ40Z50.BatteryLifetimes.CellVoltages](#blueye-protocol-BatteryBQ40Z50-BatteryLifetimes-CellVoltages) | Maximum reported cell voltages |
| min_cell_voltages | [ BatteryBQ40Z50.BatteryLifetimes.CellVoltages](#blueye-protocol-BatteryBQ40Z50-BatteryLifetimes-CellVoltages) | Minimum reported cell voltages |
| max_delta_cell_voltage | [ float](#float) | Max delta between cells (V) |
| max_charge_current | [ float](#float) | Max reported current in the charge direction (A) |
| max_discharge_current | [ float](#float) | Max reported current in the discharge direction (A) |
| max_avg_discharge_current | [ float](#float) | Max reported average current in the discharge direction (A) |
| max_avg_discharge_power | [ float](#float) | Max reported power in discharge direction (W) |
| max_cell_temperature | [ float](#float) | Max reported cell temperature (°C) |
| min_cell_temperature | [ float](#float) | Min reported cell temperature (°C) |
| max_delta_cell_temperature | [ float](#float) | Max reported temperature delta for TSx inputs configured as cell temperature (°C) |
| max_temperature_internal_sensor | [ float](#float) | Max reported internal temperature sensor temperature (°C) |
| min_temperature_internal_sensor | [ float](#float) | Min reported internal temperature sensor temperature (°C) |
| max_temperature_fet | [ float](#float) | Max reported FET temperature (°C) |

<a name="blueye-protocol-BatteryBQ40Z50-BatteryLifetimes-CellVoltages"></a>

### BatteryBQ40Z50.BatteryLifetimes.CellVoltages



| Field | Type | Description |
| ------| ---- | ----------- |
| cell_1 | [ float](#float) | Voltage for cell number 1 (V) |
| cell_2 | [ float](#float) | Voltage for cell number 2 (V) |
| cell_3 | [ float](#float) | Voltage for cell number 3 (V) |
| cell_4 | [ float](#float) | Voltage for cell number 4 (V) |

<a name="blueye-protocol-BatteryBQ40Z50-BatterySafetyEvents"></a>

### BatteryBQ40Z50.BatterySafetyEvents



| Field | Type | Description |
| ------| ---- | ----------- |
| cov_events_count | [ uint32](#uint32) | Number of cell over voltage (COV) events (events) |
| cov_last_event | [ uint32](#uint32) | Last COV event in cycle count cycles (cycles) |
| cuv_events_count | [ uint32](#uint32) | Number of cell under voltage (CUV) events (events) |
| cuv_last_event | [ uint32](#uint32) | Last CUV event in cycle count cycles (cycles) |
| ocd1_events_count | [ uint32](#uint32) | Number of over current in Discharge 1 (OCD1) events (events) |
| ocd1_last_event | [ uint32](#uint32) | Last OCD1 event in cycle count cycles (cycles) |
| ocd2_events_count | [ uint32](#uint32) | Number of over current in Discharge 2 (OCD2) events (events) |
| ocd2_last_event | [ uint32](#uint32) | Last OCD2 event in cycle count cycles (cycles) |
| occ1_events_count | [ uint32](#uint32) | Number of over current in Charge 1 (OCC1) events (events) |
| occ1_last_event | [ uint32](#uint32) | Last OCC1 event in cycle count cycles (cycles) |
| occ2_events_count | [ uint32](#uint32) | Number of over current in Charge 2 (OCC2) events (events) |
| occ2_last_event | [ uint32](#uint32) | Last OCC2 event in cycle count cycles (cycles) |
| aold_events_count | [ uint32](#uint32) | Number of Overload in discharge (AOLD) events (events) |
| aold_last_event | [ uint32](#uint32) | Last AOLD event in cycle count cycles (cycles) |
| ascd_events_count | [ uint32](#uint32) | Number of Short Circuit in Discharge (ASCD) events (events) |
| ascd_last_event | [ uint32](#uint32) | Last ASCD event in cycle count cycles (cycles) |
| ascc_events_count | [ uint32](#uint32) | Number of Short Circuit in Charge (ASCC) events (events) |
| ascc_last_event | [ uint32](#uint32) | Last ASCC event in cycle count cycles (cycles) |
| otc_events_count | [ uint32](#uint32) | Number of over temperature in Charge (OTC) events (events) |
| otc_last_event | [ uint32](#uint32) | Last OTC event in cycle count cycles (cycles) |
| otd_events_count | [ uint32](#uint32) | Number of over temperature in Discharge (OTD) events (events) |
| otd_last_event | [ uint32](#uint32) | Last OTD event in cycle count cycles (cycles) |
| otf_events_count | [ uint32](#uint32) | Number of over temperature in FET (OTF) events (events) |
| otf_last_event | [ uint32](#uint32) | Last OTF event in cycle count cycles (cycles) |

<a name="blueye-protocol-BatteryBQ40Z50-BatteryStatus"></a>

### BatteryBQ40Z50.BatteryStatus
Battery status from BQ40Z50 ref data sheet 0x16.


| Field | Type | Description |
| ------| ---- | ----------- |
| overcharged_alarm | [ bool](#bool) |  |
| terminate_charge_alarm | [ bool](#bool) |  |
| over_temperature_alarm | [ bool](#bool) |  |
| terminate_discharge_alarm | [ bool](#bool) |  |
| remaining_capacity_alarm | [ bool](#bool) |  |
| remaining_time_alarm | [ bool](#bool) |  |
| initialization | [ bool](#bool) |  |
| discharging_or_relax | [ bool](#bool) |  |
| fully_charged | [ bool](#bool) |  |
| fully_discharged | [ bool](#bool) |  |
| error | [ BatteryBQ40Z50.BatteryStatus.BatteryError](#blueye-protocol-BatteryBQ40Z50-BatteryStatus-BatteryError) | Battery error codes |

<a name="blueye-protocol-BatteryBQ40Z50-Temperature"></a>

### BatteryBQ40Z50.Temperature
Battery temperature.


| Field | Type | Description |
| ------| ---- | ----------- |
| average | [ float](#float) | Average temperature accross cells (°C) |
| cell_1 | [ float](#float) | Cell 1 temperature (°C) |
| cell_2 | [ float](#float) | Cell 2 temperature (°C) |
| cell_3 | [ float](#float) | Cell 3 temperature (°C) |
| cell_4 | [ float](#float) | Cell 4 temperature (°C) |

<a name="blueye-protocol-BatteryBQ40Z50-Voltage"></a>

### BatteryBQ40Z50.Voltage
Battery voltage levels.


| Field | Type | Description |
| ------| ---- | ----------- |
| total | [ float](#float) | Battery pack voltage level (V) |
| cell_1 | [ float](#float) | Cell 1 voltage level (V) |
| cell_2 | [ float](#float) | Vell 2 voltage level (V) |
| cell_3 | [ float](#float) | Cell 3 voltage level (V) |
| cell_4 | [ float](#float) | Cell 4 voltage level (V) |

<a name="blueye-protocol-BinlogRecord"></a>

### BinlogRecord
Wrapper message for each entry in the drone telemetry logfile.

Each entry contains the unix timestamp in UTC, the monotonic timestamp (time since boot),
and an Any message wrapping the custom Blueye message.

See separate documentation for the logfile format for more details.


| Field | Type | Description |
| ------| ---- | ----------- |
| payload | [ google.protobuf.Any](#google-protobuf-Any) | The log entry payload. |
| unix_timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Unix timestamp in UTC. |
| clock_monotonic | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Posix CLOCK_MONOTONIC timestamp. |

<a name="blueye-protocol-CPUInfo"></a>

### CPUInfo
CPU information

Contains information about the CPU load and memory usage of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| cpu_load | [ float](#float) | CPU load (0..1) |
| memory_bus_load | [ float](#float) | Memory bus load (0..1) |
| main_queue_load | [ float](#float) | Main queue load (0..1) |
| guestport_queue_load | [ float](#float) | Guestport queue load (0..1) |

<a name="blueye-protocol-CPUTemperature"></a>

### CPUTemperature
CPU temperature.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | CPU temperature (°C) |

<a name="blueye-protocol-CalibrationState"></a>

### CalibrationState
Compass calibration state.


| Field | Type | Description |
| ------| ---- | ----------- |
| status | [ CalibrationState.Status](#blueye-protocol-CalibrationState-Status) | Current calibration status |
| progress_x_positive | [ float](#float) | Progress for the positive X axis (0..1) |
| progress_x_negative | [ float](#float) | Progress for the negative X axis (0..1) |
| progress_y_positive | [ float](#float) | Progress for the positive Y axis (0..1) |
| progress_y_negative | [ float](#float) | Progress for the negative X axis (0..1) |
| progress_z_positive | [ float](#float) | Progress for the positive Z axis (0..1) |
| progress_z_negative | [ float](#float) | Progress for the negative Z axis (0..1) |
| progress_thruster | [ float](#float) | Progress for the thruster calibration (0..1) |

<a name="blueye-protocol-CameraParameters"></a>

### CameraParameters
Camera parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| h264_bitrate | [ int32](#int32) | Bitrate of the h264 stream (bit/sec) |
| mjpg_bitrate | [ int32](#int32) | Bitrate of the MJPG stream used for still pictures (bit/sec) |
| exposure | [ int32](#int32) | Shutter speed  (1/10000 * s), -1 for automatic exposure |
| white_balance | [ int32](#int32) | White balance temperature (2800..9300), -1 for automatic white balance |
| hue | [ int32](#int32) | Hue (-40..40), 0 as default |
| gain | [ float](#float) | Iso gain (0..1) |
| resolution | [ Resolution](#blueye-protocol-Resolution) | Stream, recording and image resolution |
| framerate | [ Framerate](#blueye-protocol-Framerate) | Stream and recording framerate |
| camera | [ Camera](#blueye-protocol-Camera) | Which camera the parameters belong to. |

<a name="blueye-protocol-CanisterHumidity"></a>

### CanisterHumidity
Canister humidity.

Humidity measured in the top or bottom canister of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| humidity | [ float](#float) | Air humidity (%) |

<a name="blueye-protocol-CanisterTemperature"></a>

### CanisterTemperature
Canister temperature.

Temperature measured in the top or bottom canister of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature | [ float](#float) | Temperature (°C) |

<a name="blueye-protocol-ClientInfo"></a>

### ClientInfo
Information about a remote client.


| Field | Type | Description |
| ------| ---- | ----------- |
| type | [ string](#string) | The type of client (such as Blueye App, Observer App, SDK, etc) |
| version | [ string](#string) | Client software version string |
| device_type | [ string](#string) | Device type, such as mobile, tablet, or computer |
| platform | [ string](#string) | Platform, such as iOS, Android, Linux, etc |
| platform_version | [ string](#string) | Platform software version string |
| name | [ string](#string) | Name of the client |
| is_observer | [ bool](#bool) | If the client should be connected as an observer or not |

<a name="blueye-protocol-ConnectedClient"></a>

### ConnectedClient
Information about a connected client with an id assigned by the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_id | [ uint32](#uint32) | The assigned client id |
| client_info | [ ClientInfo](#blueye-protocol-ClientInfo) | Client information. |

<a name="blueye-protocol-ConnectionDuration"></a>

### ConnectionDuration
Connection duration of a remote client.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ int32](#int32) | time since connected to drone (s) |

<a name="blueye-protocol-ControlForce"></a>

### ControlForce
Control Force is used for showing the requested control force in each direction in Newtons.


| Field | Type | Description |
| ------| ---- | ----------- |
| surge | [ float](#float) | Force in surge (N) |
| sway | [ float](#float) | Force in sway (N) |
| heave | [ float](#float) | Force in heave (N) |
| yaw | [ float](#float) | Moment in yaw (Nm) |

<a name="blueye-protocol-ControlMode"></a>

### ControlMode
Control mode from drone supervisor


| Field | Type | Description |
| ------| ---- | ----------- |
| auto_depth | [ bool](#bool) | If auto depth is enabled |
| auto_heading | [ bool](#bool) | If auto heading is enabled |
| auto_altitude | [ bool](#bool) | If auto altitude is enabled |
| station_keeping | [ bool](#bool) | If station keeping is enabled |
| weather_vaning | [ bool](#bool) | If weather vaning is enabled |
| auto_pilot_surge_yaw | [ bool](#bool) | If auto pilot surge yaw is enabled |
| auto_pilot_heave | [ bool](#bool) | If auto pilot heave is enabled |

<a name="blueye-protocol-ControllerHealth"></a>

### ControllerHealth
Controller health is used for showing the state of the controller with an relative error and load from 0 to 1.


| Field | Type | Description |
| ------| ---- | ----------- |
| depth_error | [ float](#float) | Depth error in meters (m) |
| depth_health | [ float](#float) | Depth controller load (0..1) |
| heading_error | [ float](#float) | Heading error in degrees (°) |
| heading_health | [ float](#float) | Heading controller load (0..1) |

<a name="blueye-protocol-CpProbe"></a>

### CpProbe
Reading from a Cathodic Protection Potential probe.


| Field | Type | Description |
| ------| ---- | ----------- |
| measurement | [ float](#float) | Potential measurement (V) |
| is_measurement_valid | [ bool](#bool) | Indicating if the measurement is valid |

<a name="blueye-protocol-Depth"></a>

### Depth
Water depth of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Drone depth below surface (m) |

<a name="blueye-protocol-DiveTime"></a>

### DiveTime
Amount of time the drone has been submerged.

The drone starts incrementing this value when the depth is above 250 mm.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ int32](#int32) | Number of seconds the drone has been submerged |

<a name="blueye-protocol-DroneInfo"></a>

### DroneInfo
Information about the drone.

This message contains serial numbers and version information for
internal components in the drone. Primarily used for diagnostics, or to
determine the origin of a logfile.


| Field | Type | Description |
| ------| ---- | ----------- |
| blunux_version | [ string](#string) | Blunux version string |
| serial_number | [ bytes](#bytes) | Drone serial number |
| hardware_id | [ bytes](#bytes) | Main computer unique identifier |
| model | [ Model](#blueye-protocol-Model) | Drone model |
| mb_serial | [ bytes](#bytes) | Motherboard serial number |
| bb_serial | [ bytes](#bytes) | Backbone serial number |
| ds_serial | [ bytes](#bytes) | Drone stack serial number |
| mb_uid | [ bytes](#bytes) | Motherboard unique identifier |
| bb_uid | [ bytes](#bytes) | Backbone unique identifier |
| gp | [ GuestPortInfo](#blueye-protocol-GuestPortInfo) | GuestPortInfo |
| depth_sensor | [ PressureSensorType](#blueye-protocol-PressureSensorType) | Type of depth sensor that is connected to the drone |

<a name="blueye-protocol-DvlTransducer"></a>

### DvlTransducer
DVL raw transducer data.


| Field | Type | Description |
| ------| ---- | ----------- |
| id | [ int32](#int32) | Transducer ID, 3 beams for Nucleus DVL, 4 beams for DVL A50 |
| velocity | [ float](#float) | Velocity (m/s) |
| distance | [ float](#float) | Distance (m) |
| beam_valid | [ bool](#bool) | Beam validity |
| rssi | [ float](#float) | Received signal strength indicator: strength of the signal received by this transducer (dBm) |
| nsd | [ float](#float) | Noise spectral density: strength of the background noise received by this transducer (dBm) |

<a name="blueye-protocol-DvlVelocity"></a>

### DvlVelocity
DVL raw velocity data.


| Field | Type | Description |
| ------| ---- | ----------- |
| sensor_id | [ NavigationSensorID](#blueye-protocol-NavigationSensorID) | Sensor id |
| status | [ int32](#int32) | Vendor-specific status of the DVL |
| delta_time | [ float](#float) | Time since last velocity measurement (ms) |
| fom | [ float](#float) | Figure of merit, a measure of the accuracy of the velocities (m/s) |
| velocity | [ Vector3](#blueye-protocol-Vector3) | Velocity, x forward, y left, z down (m/s) |
| is_water_tracking | [ bool](#bool) | Water tracking status |
| transducers | [repeated DvlTransducer](#blueye-protocol-DvlTransducer) | List of transducers |

<a name="blueye-protocol-ErrorFlags"></a>

### ErrorFlags
Known error states for the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| pmu_comm_ack | [ bool](#bool) | Acknowledge message not received for a message published to internal micro controller |
| pmu_comm_stream | [ bool](#bool) | Error in communication with internal micro controller |
| depth_read | [ bool](#bool) | Error reading depth sensor value |
| depth_spike | [ bool](#bool) | Sudden spike in value read from depth sensor |
| inner_pressure_read | [ bool](#bool) | Error reading inner pressure of the drone |
| inner_pressure_spike | [ bool](#bool) | Sudden spike in inner preassure |
| compass_calibration | [ bool](#bool) | Compass needs calibration |
| tilt_calibration | [ bool](#bool) | Error during calibration of tilt endpoints |
| gp1_read | [ bool](#bool) | Guest port 1 read error |
| gp2_read | [ bool](#bool) | Guest port 2 read error |
| gp3_read | [ bool](#bool) | Guest port 3 read error |
| gp1_not_flashed | [ bool](#bool) | Guest port 1 not flashed |
| gp2_not_flashed | [ bool](#bool) | Guest port 2 not flashed |
| gp3_not_flashed | [ bool](#bool) | Guest port 3 not flashed |
| gp1_unknown_device | [ bool](#bool) | Unknown device on guest port 1 |
| gp2_unknown_device | [ bool](#bool) | Unknown device on guest port 2 |
| gp3_unknown_device | [ bool](#bool) | Unknown device on guest port 3 |
| gp1_device_connection | [ bool](#bool) | Guest port 1 connection error |
| gp2_device_connection | [ bool](#bool) | Guest port 2 connection error |
| gp3_device_connection | [ bool](#bool) | Guest port 3 connection error |
| gp1_device | [ bool](#bool) | Guest port 1 device error |
| gp2_device | [ bool](#bool) | Guest port 2 device error |
| gp3_device | [ bool](#bool) | Guest port 3 device error |
| drone_serial_not_set | [ bool](#bool) | Drone serial number not set |
| drone_serial | [ bool](#bool) | Drone serial number error |
| mb_eeprom_read | [ bool](#bool) | MB eeprom read error |
| bb_eeprom_read | [ bool](#bool) | BB eeprom read error |
| mb_eeprom_not_flashed | [ bool](#bool) | MB eeprom not flashed |
| bb_eeprom_not_flashed | [ bool](#bool) | BB eeprom not flashed |
| main_camera_connection | [ bool](#bool) | We don't get buffers from the main camera |
| main_camera_firmware | [ bool](#bool) | The main camera firmware is wrong |
| guestport_camera_connection | [ bool](#bool) | We don't get buffers from the guestport camera |
| guestport_camera_firmware | [ bool](#bool) | The guestport camera firmware is wrong |
| mb_serial | [ bool](#bool) | MB serial number error |
| bb_serial | [ bool](#bool) | BB serial number error |
| ds_serial | [ bool](#bool) | DS serial number error |
| gp_current_read | [ bool](#bool) | Error reading GP current |
| gp_current | [ bool](#bool) | Max GP current exceeded |
| gp1_bat_current | [ bool](#bool) | Max battery current exceeded on GP1 |
| gp2_bat_current | [ bool](#bool) | Max battery current exceeded on GP2 |
| gp3_bat_current | [ bool](#bool) | Max battery current exceeded on GP3 |
| gp_20v_current | [ bool](#bool) | Max 20V current exceeded on GP |
| dvl_thermal_protection_mode | [ bool](#bool) | DVL is in thermal protection mode |
| dvl_no_power | [ bool](#bool) | GP protection has been triggered at boot or faulty DVL |
| usb_disconnect | [ bool](#bool) | USB disconnect |
| video_urb_error | [ bool](#bool) | Video URB error |

<a name="blueye-protocol-ForwardDistance"></a>

### ForwardDistance
Distance to an object in front of the drone

Typically obtained from a 1D pinger.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Distance in front of drone (m) |
| is_valid | [ bool](#bool) | If distance reading is valid or not |

<a name="blueye-protocol-GenericServo"></a>

### GenericServo
Servo message used to represent the angle of the servo.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Servo value (0..1) |
| guest_port_number | [ GuestPortNumber](#blueye-protocol-GuestPortNumber) | Guest port the servo is on |

<a name="blueye-protocol-GripperVelocities"></a>

### GripperVelocities
Gripper velocity values.


| Field | Type | Description |
| ------| ---- | ----------- |
| grip_velocity | [ float](#float) | The gripping velocity (-1.0..1.0) |
| rotate_velocity | [ float](#float) | The rotating velocity (-1.0..1.0) |

<a name="blueye-protocol-GuestPortConnectorInfo"></a>

### GuestPortConnectorInfo
GuestPort connector information.


| Field | Type | Description |
| ------| ---- | ----------- |
| <small><strong>oneof</strong> <code>connected_device</code></small><br>device_list | [ GuestPortDeviceList](#blueye-protocol-GuestPortDeviceList) | List of devices on this connector |
| <small><strong>oneof</strong> <code>connected_device</code></small><br>error | [ GuestPortError](#blueye-protocol-GuestPortError) | Guest port connector error |
| guest_port_number | [ GuestPortNumber](#blueye-protocol-GuestPortNumber) | Guest port the connector is connected to |

<a name="blueye-protocol-GuestPortCurrent"></a>

### GuestPortCurrent
GuestPort current readings.


| Field | Type | Description |
| ------| ---- | ----------- |
| gp1_bat | [ double](#double) | Current on GP1 battery voltage (A) |
| gp2_bat | [ double](#double) | Current on GP2 battery voltage (A) |
| gp3_bat | [ double](#double) | Current on GP3 battery voltage (A) |
| gp_20v | [ double](#double) | Current on common 20V supply (A) |

<a name="blueye-protocol-GuestPortDevice"></a>

### GuestPortDevice
GuestPort device.


| Field | Type | Description |
| ------| ---- | ----------- |
| device_id | [ GuestPortDeviceID](#blueye-protocol-GuestPortDeviceID) | Blueye device identifier |
| manufacturer | [ string](#string) | Manufacturer name |
| name | [ string](#string) | Device name |
| serial_number | [ string](#string) | Serial number |
| depth_rating | [ float](#float) | Depth rating (m) |
| required_blunux_version | [ string](#string) | Required Blunux version (x.y.z) |
| detach_status | [ GuestPortDetachStatus](#blueye-protocol-GuestPortDetachStatus) | Detach status based on detection pin |

<a name="blueye-protocol-GuestPortDeviceList"></a>

### GuestPortDeviceList
List of guest port devices.


| Field | Type | Description |
| ------| ---- | ----------- |
| devices | [repeated GuestPortDevice](#blueye-protocol-GuestPortDevice) | List of guest port devices |

<a name="blueye-protocol-GuestPortInfo"></a>

### GuestPortInfo
GuestPort information.


| Field | Type | Description |
| ------| ---- | ----------- |
| gp1 | [ GuestPortConnectorInfo](#blueye-protocol-GuestPortConnectorInfo) | GuestPortConnectorInfo 1 |
| gp2 | [ GuestPortConnectorInfo](#blueye-protocol-GuestPortConnectorInfo) | GuestPortConnectorInfo 2 |
| gp3 | [ GuestPortConnectorInfo](#blueye-protocol-GuestPortConnectorInfo) | GuestPortConnectorInfo 3 |

<a name="blueye-protocol-GuestPortRestartInfo"></a>

### GuestPortRestartInfo
GuestPort restart information.


| Field | Type | Description |
| ------| ---- | ----------- |
| power_off_duration | [ double](#double) | Duration to keep the guest ports off (s) |

<a name="blueye-protocol-Imu"></a>

### Imu
Imu data in drone body frame

x - forward
y - right
z - down


| Field | Type | Description |
| ------| ---- | ----------- |
| accelerometer | [ Vector3](#blueye-protocol-Vector3) | Acceleration (g) |
| gyroscope | [ Vector3](#blueye-protocol-Vector3) | Angular velocity (rad/s) |
| magnetometer | [ Vector3](#blueye-protocol-Vector3) | Magnetic field (μT) |
| temperature | [ float](#float) | Temperature (°C) |

<a name="blueye-protocol-IperfStatus"></a>

### IperfStatus
Connection speed between drone and Surface Unit.


| Field | Type | Description |
| ------| ---- | ----------- |
| sent | [ float](#float) | Transfer rate from drone to Surface Unit (Mbit/s) |
| received | [ float](#float) | Transfer rate from Surface Unit to drone (Mbit/s) |

<a name="blueye-protocol-Laser"></a>

### Laser
Laser message used to represent the intensity of connected laser.

If the laser does not support dimming but only on and off,
a value of 0 turns the laser off, and any value above 0
turns the laser on.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Laser intensity, any value above 0 turns the laser on (0..1) |

<a name="blueye-protocol-LatLongPosition"></a>

### LatLongPosition
Latitude and longitude position in WGS 84 decimal degrees format.


| Field | Type | Description |
| ------| ---- | ----------- |
| latitude | [ double](#double) | Latitude (°) |
| longitude | [ double](#double) | Longitude (°) |

<a name="blueye-protocol-Lights"></a>

### Lights
Lights message used to represent the intensity of the main light or external lights.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Light intensity (0..1) |

<a name="blueye-protocol-MedusaSpectrometerData"></a>

### MedusaSpectrometerData
Medusa gamma ray sensor spectrometer data


| Field | Type | Description |
| ------| ---- | ----------- |
| drone_time | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Time stamp when the data is received |
| sensor_time | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Time stamp the sensor reports |
| realtime | [ float](#float) | Time the sensor actually measured (s) |
| livetime | [ float](#float) | Time the measurement took (s) |
| total | [ uint32](#uint32) | Total counts inside the spectrum |
| countrate | [ uint32](#uint32) | Counts per second inside the spectrum (rounded) |
| cosmics | [ uint32](#uint32) | Detected counts above the last channel |

<a name="blueye-protocol-MotionInput"></a>

### MotionInput
Motion input from client.

Used to indicate the desired motion in each direction.
Typically these values map to the left and right joystick for motion,
and the left and right trigger for the slow and boost modifiers.


| Field | Type | Description |
| ------| ---- | ----------- |
| surge | [ float](#float) | Forward (positive) and backwards (negative) movement. (-1..1) |
| sway | [ float](#float) | Right (positive) and left (negative) lateral movement (-1..1) |
| heave | [ float](#float) | Descend (positive) and ascend (negative) movement (-1..1) |
| roll | [ float](#float) | Roll left (negative) or right (positive). (-1..1) |
| pitch | [ float](#float) | Pitch down (negative) or up (positive). (-1..1) |
| yaw | [ float](#float) | Left (positive) and right (negative) movement (-1..1) |
| slow | [ float](#float) | Multiplier used to reduce the speed of the motion (0..1) |
| boost | [ float](#float) | Multiplier used to increase the speed of the motion (0..1) |

<a name="blueye-protocol-MultibeamConfig"></a>

### MultibeamConfig
Configuration message for sonar devices


| Field | Type | Description |
| ------| ---- | ----------- |
| frequency_mode | [ MultibeamFrequencyMode](#blueye-protocol-MultibeamFrequencyMode) | Frequency mode used by the sonar if supported |
| ping_rate | [ MultibeamConfig.PingRate](#blueye-protocol-MultibeamConfig-PingRate) | Sets the maximum ping rate. |
| gamma_correction | [ double](#double) | Gamma correction (0..1.0) |
| gain_assist | [ bool](#bool) | Enable gain assist |
| maximum_number_of_beams | [ MultibeamConfig.MaximumNumberOfBeams](#blueye-protocol-MultibeamConfig-MaximumNumberOfBeams) | Maximum number of beams. Used to throttle bandwidth. |
| range | [ double](#double) | The range demand (m) |
| gain | [ double](#double) | The gain demand (0..1) |
| salinity | [ double](#double) | Set water salinity (ppt). Defaults to zero in fresh water |
| device_id | [ GuestPortDeviceID](#blueye-protocol-GuestPortDeviceID) | Device ID of the sonar |
| bandwidth_limit | [ uint32](#uint32) | Network bandwidth limit (Mbit/s). Applies only to Oculus devices. |

<a name="blueye-protocol-MultibeamDiscovery"></a>

### MultibeamDiscovery
Discovery message for sonar devices


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If the sonar driver is enabled |
| ip | [ string](#string) | IP address of the sonar |
| mask | [ string](#string) | Subnet mask of the sonar |
| serial_number | [ string](#string) | Serial number of the sonar |
| fw_version | [ string](#string) | Firmware version of the sonar |
| connected_ip | [ string](#string) | IP address of the connected device |
| device_id | [ GuestPortDeviceID](#blueye-protocol-GuestPortDeviceID) | Device ID of the sonar |

<a name="blueye-protocol-MultibeamFrameOffset"></a>

### MultibeamFrameOffset
Frame offset for multibeam recordings index cache


| Field | Type | Description |
| ------| ---- | ----------- |
| duration | [ google.protobuf.Duration](#google-protobuf-Duration) | Duration from the start of the recording |
| offset | [ int64](#int64) | Offset in bytes from the start of the file |

<a name="blueye-protocol-MultibeamPing"></a>

### MultibeamPing
Multibeam sonar ping

Contains all the information for rendering a multibeam sonar frame


| Field | Type | Description |
| ------| ---- | ----------- |
| range | [ double](#double) | Maximum range value (m) |
| gain | [ double](#double) | Percentage of gain (0 to 1) |
| frequency | [ double](#double) | Ping acoustic frequency (Hz) |
| speed_of_sound_used | [ double](#double) | Speed of sound used by the sonar for range calculations (m/s) |
| frequency_mode | [ MultibeamFrequencyMode](#blueye-protocol-MultibeamFrequencyMode) | Frequency mode used by the sonar for this frame |
| number_of_ranges | [ uint32](#uint32) | Height of the ping image data. |
| number_of_beams | [ uint32](#uint32) | Width of the ping image data. |
| step | [ uint32](#uint32) | Size in bytes of each row in the ping data image. |
| bearings | [repeated float](#float) | Bearing angle of each column of the sonar data<br>(in 100th of a degree, multiply by 0.01 to get a value in degrees).<br>The sonar image is not sampled uniformly in the bearing direction. |
| ping_data | [ bytes](#bytes) | Ping data (row major, 2D, grayscale image) |
| device_id | [ GuestPortDeviceID](#blueye-protocol-GuestPortDeviceID) | Device ID of the sonar |
| frame_generation_timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Timestamp when the frame was generated |

<a name="blueye-protocol-MultibeamServo"></a>

### MultibeamServo
Servo message used to represent the angle of the servo.


| Field | Type | Description |
| ------| ---- | ----------- |
| angle | [ float](#float) | Servo degrees (-30..30) |

<a name="blueye-protocol-MutltibeamRecordingIndex"></a>

### MutltibeamRecordingIndex
Multibeam recording index cache


| Field | Type | Description |
| ------| ---- | ----------- |
| frame_offsets | [repeated MultibeamFrameOffset](#blueye-protocol-MultibeamFrameOffset) | List of frame offsets |

<a name="blueye-protocol-NStreamers"></a>

### NStreamers
Number of spectators connected to video stream.


| Field | Type | Description |
| ------| ---- | ----------- |
| main | [ int32](#int32) | The number of clients to the main camera stream |
| guestport | [ int32](#int32) | The number of clients to the guestport camera stream |

<a name="blueye-protocol-NavigationSensorStatus"></a>

### NavigationSensorStatus
Navigation sensor used in the position observer with validity state


| Field | Type | Description |
| ------| ---- | ----------- |
| sensor_id | [ NavigationSensorID](#blueye-protocol-NavigationSensorID) | Sensor id |
| is_valid | [ bool](#bool) | Sensor validity |
| northing | [ float](#float) | Position from reset point (m) |
| easting | [ float](#float) | Position from reset point (m) |
| heading | [ float](#float) | Heading from sensor (-pi..pi) |
| fom | [ float](#float) | Figure of merit |
| std | [ float](#float) | Standard deviation |
| global_position | [ LatLongPosition](#blueye-protocol-LatLongPosition) | Global position from sensor |

<a name="blueye-protocol-Notification"></a>

### Notification
Notification is used for displaying info, warnings, and errors to the user.


| Field | Type | Description |
| ------| ---- | ----------- |
| type | [ NotificationType](#blueye-protocol-NotificationType) | Notification to be displayed to the user |
| level | [ NotificationLevel](#blueye-protocol-NotificationLevel) | Level of the notification, info, warning or error |
| value | [ google.protobuf.Any](#google-protobuf-Any) | Optional value to be displayed in the message |
| timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Timestamp of the notification |

<a name="blueye-protocol-OverlayParameters"></a>

### OverlayParameters
Overlay parameters.

All available parameters that can be used to configure telemetry overlay on video recordings.


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature_enabled | [ bool](#bool) | If temperature should be included |
| depth_enabled | [ bool](#bool) | If depth should be included |
| heading_enabled | [ bool](#bool) | If heading should be included |
| tilt_enabled | [ bool](#bool) | If camera tilt angle should be included |
| thickness_enabled | [ bool](#bool) | If camera tilt angle should be included |
| date_enabled | [ bool](#bool) | If date should be included |
| distance_enabled | [ bool](#bool) | If distance should be included |
| altitude_enabled | [ bool](#bool) | If altitude should be included |
| cp_probe_enabled | [ bool](#bool) | If cp-probe should be included |
| medusa_enabled | [ bool](#bool) | If medusa measurement should be included |
| drone_location_enabled | [ bool](#bool) | If the drone location coordinates should be included |
| logo_type | [ LogoType](#blueye-protocol-LogoType) | Which logo should be used |
| depth_unit | [ DepthUnit](#blueye-protocol-DepthUnit) | Which unit should be used for depth: Meter, Feet or None |
| temperature_unit | [ TemperatureUnit](#blueye-protocol-TemperatureUnit) | Which unit should be used for temperature: Celsius or Fahrenheit |
| thickness_unit | [ ThicknessUnit](#blueye-protocol-ThicknessUnit) | Which unit should be used for thickness: Millimeters or Inches |
| timezone_offset | [ int32](#int32) | Timezone offset from UTC (min) |
| margin_width | [ int32](#int32) | Horizontal margins of text elements (px) |
| margin_height | [ int32](#int32) | Vertical margins of text elements (px) |
| font_size | [ FontSize](#blueye-protocol-FontSize) | Font size of text elements |
| title | [ string](#string) | Optional title |
| subtitle | [ string](#string) | Optional subtitle |
| date_format | [ string](#string) | Posix strftime format string for time stamp |
| shading | [ float](#float) | Pixel intensity to subtract from text background (0..1), 0: transparent, 1: black |

<a name="blueye-protocol-PersistentStorageSettings"></a>

### PersistentStorageSettings
PersistentStorageSettings defines settings for writing various types of data in the persistent storage on the drone

Some of the data is written during factory calibration (acc calibration), while other data is written during user
calubration or during normal operation.


| Field | Type | Description |
| ------| ---- | ----------- |
| videos | [ bool](#bool) | Indicates if videos should be written to the video partition. |
| images | [ bool](#bool) | Indicates if images should be written to the video partition. |
| binlog | [ bool](#bool) | Indicates if binary logs with telemetry data should be written to the data partition. |
| multibeam | [ bool](#bool) | Indicates if multibeam data should be written to the video partition. |
| webserver_log | [ bool](#bool) | Indicates if webserver logs should be written to the data partition. |
| control_system_log | [ bool](#bool) | Indicates if control system logs should be written to the data partition. |
| gyro_calibration | [ bool](#bool) | Indicates if gyro calibration data should be written to the data partition. |
| compass_calibration | [ bool](#bool) | Indicates if compass calibration data should be written to the data partition. |
| acc_calibration | [ bool](#bool) | Indicates if accelerometer calibration data should be written to the data partition. |

<a name="blueye-protocol-PingerConfiguration"></a>

### PingerConfiguration
Pinger configuration.

Used to specify the configuration the BR 1D-Pinger.


| Field | Type | Description |
| ------| ---- | ----------- |
| mounting_direction | [ PingerConfiguration.MountingDirection](#blueye-protocol-PingerConfiguration-MountingDirection) | Mounting direction of the pinger |

<a name="blueye-protocol-PositionEstimate"></a>

### PositionEstimate
Position estimate from the Extended Kalman filter based observer if a DVL is connected.


| Field | Type | Description |
| ------| ---- | ----------- |
| northing | [ float](#float) | Position from reset point (m) |
| easting | [ float](#float) | Position from reset point (m) |
| heading | [ float](#float) | Continuous heading estimate (rad) |
| surge_rate | [ float](#float) | Velocity in surge (m/s) |
| sway_rate | [ float](#float) | Velocity in sway (m/s) |
| yaw_rate | [ float](#float) | Rotaion rate in yaw (rad/s) |
| ocean_current | [ float](#float) | Estimated ocean current (m/s) |
| odometer | [ float](#float) | Travelled distance since reset (m) |
| is_valid | [ bool](#bool) | If the estimate can be trusted |
| global_position | [ LatLongPosition](#blueye-protocol-LatLongPosition) | Best estimate of the global position in decimal degrees |
| navigation_sensors | [repeated NavigationSensorStatus](#blueye-protocol-NavigationSensorStatus) | List of available sensors with status |
| speed_over_ground | [ float](#float) | Speed over ground (m/s) |
| course_over_ground | [ float](#float) | Course over ground (°) |
| time_since_reset_sec | [ int32](#int32) | Time since reset (s) |

<a name="blueye-protocol-RecordOn"></a>

### RecordOn
Which cameras are supposed to be recording


| Field | Type | Description |
| ------| ---- | ----------- |
| main | [ bool](#bool) | Record the main camera |
| guestport | [ bool](#bool) | Record external camera |
| multibeam | [ bool](#bool) | Record multibeam |

<a name="blueye-protocol-RecordState"></a>

### RecordState
Camera recording state.


| Field | Type | Description |
| ------| ---- | ----------- |
| main_is_recording | [ bool](#bool) | If the main camera is recording |
| main_seconds | [ int32](#int32) | Main record time (s) |
| main_fps | [ float](#float) | Main record fps |
| guestport_is_recording | [ bool](#bool) | If the guestport camera is recording |
| guestport_seconds | [ int32](#int32) | Guestport record time (s) |
| guestport_fps | [ float](#float) | Guestport record fps |
| multibeam_is_recording | [ bool](#bool) | If the multibeam is recording |
| multibeam_seconds | [ int32](#int32) | Multibeam record time (s) |
| multibeam_fps | [ float](#float) | Multibeam record fps |

<a name="blueye-protocol-Reference"></a>

### Reference
Reference for the control system.
Note that the internal heading reference is not relative to North, use
(ControlHealth.heading_error + pose.yaw) instead.


| Field | Type | Description |
| ------| ---- | ----------- |
| surge | [ float](#float) | Reference from joystick surge input (0..1) |
| sway | [ float](#float) | Reference from joystick sway input (0..1) |
| heave | [ float](#float) | Reference from joystick heave input (0..1) |
| yaw | [ float](#float) | Reference from joystick yaw input (0..1) |
| depth | [ float](#float) | Reference drone depth below surface (m) |
| heading | [ float](#float) | Reference used in auto heading mode, gyro based (°) |
| altitude | [ float](#float) | Reference used in auto altitude mode (m) |

<a name="blueye-protocol-ResetPositionSettings"></a>

### ResetPositionSettings
ResetPositionSettings used during reset of the position estimate.


| Field | Type | Description |
| ------| ---- | ----------- |
| heading_source_during_reset | [ HeadingSource](#blueye-protocol-HeadingSource) | Option to use the drone compass or due North as heading during reset |
| manual_heading | [ float](#float) | Heading in degrees (0-359) |
| reset_coordinate_source | [ ResetCoordinateSource](#blueye-protocol-ResetCoordinateSource) | Option to use the device GPS or a manual coordinate. |
| reset_coordinate | [ LatLongPosition](#blueye-protocol-LatLongPosition) | Reset coordinate in decimal degrees |

<a name="blueye-protocol-StationKeepingState"></a>

### StationKeepingState
Station keeping state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If station keeping is enabled |

<a name="blueye-protocol-StorageSpace"></a>

### StorageSpace
Storage space.


| Field | Type | Description |
| ------| ---- | ----------- |
| total_space | [ int64](#int64) | Total bytes of storage space (B) |
| free_space | [ int64](#int64) | Available bytes of storage space (B) |

<a name="blueye-protocol-SystemTime"></a>

### SystemTime
System time.


| Field | Type | Description |
| ------| ---- | ----------- |
| unix_timestamp | [ google.protobuf.Timestamp](#google-protobuf-Timestamp) | Unix timestamp |

<a name="blueye-protocol-ThicknessGauge"></a>

### ThicknessGauge
Thickness measurement data from a Cygnus Thickness Gauge.


| Field | Type | Description |
| ------| ---- | ----------- |
| thickness_measurement | [ float](#float) | Thickness measurement of a steel plate |
| echo_count | [ uint32](#uint32) | Indicating the quality of the reading when invalid (0-3) |
| sound_velocity | [ uint32](#uint32) | Speed of sound in the steel member (m/s) |
| is_measurement_valid | [ bool](#bool) | Indicating if the measurement is valid |

<a name="blueye-protocol-TiltAngle"></a>

### TiltAngle
Angle of tilt camera in degrees.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Tilt angle (°) |

<a name="blueye-protocol-TiltStabilizationState"></a>

### TiltStabilizationState
Tilt stabilization state.

Blueye drones with mechanical tilt has the ability to enable
camera stabilization.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If tilt stabilization is enabled |

<a name="blueye-protocol-TiltVelocity"></a>

### TiltVelocity
Relative velocity of tilt


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Relative angular velocity of tilt (-1..1), negative means down and positive means up |

<a name="blueye-protocol-TimeLapseState"></a>

### TimeLapseState
Time-lapse state published if time-lapse mission is running.


| Field | Type | Description |
| ------| ---- | ----------- |
| interval | [ float](#float) | Interval between photos |
| photos_taken | [ int32](#int32) | Number of photos taken |
| interval_type | [ IntervalType](#blueye-protocol-IntervalType) | Interval type for photos, distance or time |

<a name="blueye-protocol-Vector3"></a>

### Vector3
Vector with 3 elements


| Field | Type | Description |
| ------| ---- | ----------- |
| x | [ double](#double) | x-component |
| y | [ double](#double) | y-component |
| z | [ double](#double) | z-component |

<a name="blueye-protocol-WaterDensity"></a>

### WaterDensity
Water density.

Used to specify the water density the drone is operating in,
to achieve more accurate depth measurements, f. ex. influenced by salinity.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Water density (g/l) |

<a name="blueye-protocol-WaterTemperature"></a>

### WaterTemperature
Water temperature measured by the drone's combined depth and temperature sensor.


| Field | Type | Description |
| ------| ---- | ----------- |
| value | [ float](#float) | Water temperature (°C) |

<a name="blueye-protocol-WeatherVaningState"></a>

### WeatherVaningState
Weather vaning state.


| Field | Type | Description |
| ------| ---- | ----------- |
| enabled | [ bool](#bool) | If weather vaning is enabled |



<a name="blueye-protocol-BatteryBQ40Z50-BatteryStatus-BatteryError"></a>

### BatteryBQ40Z50.BatteryStatus.BatteryError
Battery error code from BQ40Z50 BMS data sheet.

| Name | Number | Description |
| ---- | ------ | ----------- |
| BATTERY_ERROR_UNSPECIFIED | 0 |  |
| BATTERY_ERROR_OK | 1 |  |
| BATTERY_ERROR_BUSY | 2 |  |
| BATTERY_ERROR_RESERVED_COMMAND | 3 |  |
| BATTERY_ERROR_UNSUPPORTED_COMMAND | 4 |  |
| BATTERY_ERROR_ACCESS_DENIED | 5 |  |
| BATTERY_ERROR_OVERFLOW_UNDERFLOW | 6 |  |
| BATTERY_ERROR_BAD_SIZE | 7 |  |
| BATTERY_ERROR_UNKNOWN_ERROR | 8 |  |



<a name="blueye-protocol-CalibrationState-Status"></a>

### CalibrationState.Status
Status of the compass calibration procedure.

When calibration is started, the status will indicate the active (upfacing) axis.

| Name | Number | Description |
| ---- | ------ | ----------- |
| STATUS_UNSPECIFIED | 0 | Unspecified status |
| STATUS_NOT_CALIBRATING | 1 | Compass is not currently calibrating |
| STATUS_CALIBRATING_NO_AXIS | 2 | Compass is calibrating but active calibration axis cannot be determined |
| STATUS_CALIBRATING_X_POSITIVE | 3 | Compass is calibrating and the positive X axis is active |
| STATUS_CALIBRATING_X_NEGATIVE | 4 | Compass is calibrating and the negative X axis is active |
| STATUS_CALIBRATING_Y_POSITIVE | 5 | Compass is calibrating and the positive Y axis is active |
| STATUS_CALIBRATING_Y_NEGATIVE | 6 | Compass is calibrating and the negative Y axis is active |
| STATUS_CALIBRATING_Z_POSITIVE | 7 | Compass is calibrating and the positive Z axis is active |
| STATUS_CALIBRATING_Z_NEGATIVE | 8 | Compass is calibrating and the negative Z axis is active |
| STATUS_CALIBRATING_THRUSTER | 9 | Compass is calibrating for thruster interferance |



<a name="blueye-protocol-Camera"></a>

### Camera
Which camera to control.

| Name | Number | Description |
| ---- | ------ | ----------- |
| CAMERA_UNSPECIFIED | 0 | Camera not specified |
| CAMERA_MAIN | 1 | Main camera |
| CAMERA_GUESTPORT | 2 | Guestport camera |



<a name="blueye-protocol-DepthUnit"></a>

### DepthUnit
Available depth units.

| Name | Number | Description |
| ---- | ------ | ----------- |
| DEPTH_UNIT_UNSPECIFIED | 0 | Depth unit not specified |
| DEPTH_UNIT_METERS | 1 | Depth should be displayed as meters |
| DEPTH_UNIT_FEET | 2 | Depth should be displayed as feet |



<a name="blueye-protocol-FontSize"></a>

### FontSize
Available font sizes for overlay text elements.

| Name | Number | Description |
| ---- | ------ | ----------- |
| FONT_SIZE_UNSPECIFIED | 0 | Font size not specified |
| FONT_SIZE_PX15 | 1 | 15 px |
| FONT_SIZE_PX20 | 2 | 20 px |
| FONT_SIZE_PX25 | 3 | 25 px |
| FONT_SIZE_PX30 | 4 | 30 px |
| FONT_SIZE_PX35 | 5 | 35 px |
| FONT_SIZE_PX40 | 6 | 40 px |



<a name="blueye-protocol-Framerate"></a>

### Framerate
Available camera frame rates.

| Name | Number | Description |
| ---- | ------ | ----------- |
| FRAMERATE_UNSPECIFIED | 0 | Framerate not specified |
| FRAMERATE_FPS_30 | 1 | 30 frames per second |
| FRAMERATE_FPS_25 | 2 | 25 frames per second |



<a name="blueye-protocol-GuestPortDetachStatus"></a>

### GuestPortDetachStatus
GuestPort detach status.

| Name | Number | Description |
| ---- | ------ | ----------- |
| GUEST_PORT_DETACH_STATUS_UNSPECIFIED | 0 | Unspecified (Default for non-detachable devices) |
| GUEST_PORT_DETACH_STATUS_ATTACHED | 1 | Detachable device attached |
| GUEST_PORT_DETACH_STATUS_DETACHED | 2 | Detachable device detached |



<a name="blueye-protocol-GuestPortDeviceID"></a>

### GuestPortDeviceID
GuestPort device ID.

| Name | Number | Description |
| ---- | ------ | ----------- |
| GUEST_PORT_DEVICE_ID_UNSPECIFIED | 0 | Unspecified |
| GUEST_PORT_DEVICE_ID_BLIND_PLUG | 1 | Blueye blind plug |
| GUEST_PORT_DEVICE_ID_TEST_STATION | 2 | Blueye test station |
| GUEST_PORT_DEVICE_ID_DEBUG_SERIAL | 3 | Blueye debug serial |
| GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT | 4 | Blueye Light |
| GUEST_PORT_DEVICE_ID_BLUEYE_CAM | 5 | Blueye Cam |
| GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_LUMEN | 6 | Blue Robotics Lumen |
| GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_NEWTON | 7 | Blue Robotics Newton |
| GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_PING_SONAR | 8 | Blue Robotics Ping Sonar |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_LAB_REACH_ALPHA | 9 | Blueprint Lab Reach Alpha |
| GUEST_PORT_DEVICE_ID_WATERLINKED_DVL_A50 | 10 | Waterlinked DVL A50 |
| GUEST_PORT_DEVICE_ID_IMPACT_SUBSEA_ISS360 | 11 | Impact Subsea ISS360 Sonar |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_SEATRAC_X010 | 12 | Blueprint Subsea Seatrac X110 |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_OCULUS_M750D | 13 | Blueprint Subsea Oculus M750d |
| GUEST_PORT_DEVICE_ID_CYGNUS_MINI_ROV_THICKNESS_GAUGE | 14 | Cygnus Mini ROV Thickness Gauge |
| GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_PING360_SONAR | 15 | Blue Robotics Ping360 Scanning Imaging Sonar |
| GUEST_PORT_DEVICE_ID_TRITECH_GEMINI_720IM | 16 | Tritech Gemini 720im Multibeam Sonar |
| GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT_PAIR | 17 | Blueye Light Pair |
| GUEST_PORT_DEVICE_ID_TRITECH_GEMINI_MICRON | 18 | Tritech Micron Gemini |
| GUEST_PORT_DEVICE_ID_OCEAN_TOOLS_DIGICP | 19 | Ocean Tools DigiCP |
| GUEST_PORT_DEVICE_ID_TRITECH_GEMINI_720IK | 20 | Tritech Gemini 720ik Multibeam Sonar |
| GUEST_PORT_DEVICE_ID_NORTEK_NUCLEUS_1000 | 21 | Nortek Nucleus 1000 DVL |
| GUEST_PORT_DEVICE_ID_BLUEYE_GENERIC_SERVO | 22 | Blueye Generic Servo |
| GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_SERVO | 23 | Blueye Multibeam Skid Servo |
| GUEST_PORT_DEVICE_ID_BLUE_ROBOTICS_DETACHABLE_NEWTON | 24 | Detachable Blue Robotics Newton |
| GUEST_PORT_DEVICE_ID_INSITU_AQUA_TROLL_500 | 25 | In-Situ Aqua TROLL 500 |
| GUEST_PORT_DEVICE_ID_MEDUSA_RADIOMETRICS_MS100 | 26 | Medusa Radiometrics Gamma Ray Sensor |
| GUEST_PORT_DEVICE_ID_LASER_TOOLS_SEA_BEAM | 27 | Laser Tools Sea Beam Underwater Laser |
| GUEST_PORT_DEVICE_ID_SPOT_X_LASER_SCALERS | 28 | Spot X Laser Scalers |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_OCULUS_M1200D | 29 | Blueprint Subsea Oculus M1200d |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_OCULUS_M3000D | 30 | Blueprint Subsea Oculus M3000d |
| GUEST_PORT_DEVICE_ID_INSITU_AQUA_TROLL_100 | 31 | In-Situ Aqua TROLL 100 |
| GUEST_PORT_DEVICE_ID_INSITU_RDO_PRO_X | 32 | In-Situ RDO PRO-X |
| GUEST_PORT_DEVICE_ID_INSITU_RDO_BLUE | 33 | In-Situ RDO Blue |
| GUEST_PORT_DEVICE_ID_BLUEYE_CAMERA_SERVO | 34 | Blueye Camera Servo |
| GUEST_PORT_DEVICE_ID_BLUEYE_MULTIBEAM_HEAD_SERVO | 35 | Blueye Multibeam Head Servo |
| GUEST_PORT_DEVICE_ID_CERULEAN_OMNISCAN_450FS | 36 | Cerulean Omniscan 450 FS |
| GUEST_PORT_DEVICE_ID_CERULEAN_OMNISCAN_450SS | 37 | Cerulean Omniscan 450 SS |
| GUEST_PORT_DEVICE_ID_BLUEYE_GNSS_DEVICE | 38 | Blueye GNSS device |
| GUEST_PORT_DEVICE_ID_WATERLINKED_DVL_A50_600 | 39 | Waterlinked DVL A50 600m |
| GUEST_PORT_DEVICE_ID_IMAGENEX_831L | 40 | Imagenex 831L Pipe Profiling Sonar |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_OCULUS_C550D | 41 | Blueprint Subsea Oculus C550d |
| GUEST_PORT_DEVICE_ID_BLUEPRINT_SUBSEA_OCULUS_M370S | 42 | Blueprint Subsea Oculus M370s |



<a name="blueye-protocol-GuestPortError"></a>

### GuestPortError
GuestPort error. Only indicated errors on the guest port connector itself.

| Name | Number | Description |
| ---- | ------ | ----------- |
| GUEST_PORT_ERROR_UNSPECIFIED | 0 | Unspecified value |
| GUEST_PORT_ERROR_NOT_CONNECTED | 1 | Device not connected |
| GUEST_PORT_ERROR_READ_ERROR | 2 | EEPROM read error |
| GUEST_PORT_ERROR_NOT_FLASHED | 3 | Connector not flashed |
| GUEST_PORT_ERROR_CRC_ERROR | 4 | Wrong CRC for protobuf message |
| GUEST_PORT_ERROR_PARSE_ERROR | 5 | Protobuf message cannot be parsed |



<a name="blueye-protocol-GuestPortNumber"></a>

### GuestPortNumber
GuestPort number.

| Name | Number | Description |
| ---- | ------ | ----------- |
| GUEST_PORT_NUMBER_UNSPECIFIED | 0 | Unspecified |
| GUEST_PORT_NUMBER_PORT_1 | 1 | Guest port 1 |
| GUEST_PORT_NUMBER_PORT_2 | 2 | Guest port 2 |
| GUEST_PORT_NUMBER_PORT_3 | 3 | Guest port 3 |



<a name="blueye-protocol-HeadingSource"></a>

### HeadingSource
Heading source used during reset of the position estimate.

| Name | Number | Description |
| ---- | ------ | ----------- |
| HEADING_SOURCE_UNSPECIFIED | 0 | Unspecified |
| HEADING_SOURCE_DRONE_COMPASS | 1 | Uses the drone compass to set the heading |
| HEADING_SOURCE_MANUAL_INPUT | 2 | Used when the user sets the heading manually |



<a name="blueye-protocol-IntervalType"></a>

### IntervalType
Interval type for time-lapse photos.

| Name | Number | Description |
| ---- | ------ | ----------- |
| INTERVAL_TYPE_UNSPECIFIED | 0 | Unspecified |
| INTERVAL_TYPE_TIME | 1 | Time interval |
| INTERVAL_TYPE_DISTANCE | 2 | Distance interval |



<a name="blueye-protocol-LogoType"></a>

### LogoType
Available logo types.

| Name | Number | Description |
| ---- | ------ | ----------- |
| LOGO_TYPE_UNSPECIFIED | 0 | Logo type not specified |
| LOGO_TYPE_NONE | 1 | Do not add any logo |
| LOGO_TYPE_DEFAULT | 2 | Add default logo |
| LOGO_TYPE_CUSTOM | 3 | Add user defined logo |



<a name="blueye-protocol-Model"></a>

### Model
Drone models produced by Blueye

| Name | Number | Description |
| ---- | ------ | ----------- |
| MODEL_UNSPECIFIED | 0 | ModelName not specified |
| MODEL_PIONEER | 1 | Blueye Pioneer, the first model |
| MODEL_PRO | 2 | Blueye Pro, features camera tilt |
| MODEL_X1 | 4 | Blueye X1, features camera tilt and one guest port |
| MODEL_X3 | 3 | Blueye X3, features support for peripherals |
| MODEL_X3_ULTRA | 6 | Blueye X3 Ultra |
| MODEL_NEXT | 5 | Blueye ? |



<a name="blueye-protocol-MultibeamConfig-MaximumNumberOfBeams"></a>

### MultibeamConfig.MaximumNumberOfBeams


| Name | Number | Description |
| ---- | ------ | ----------- |
| MAXIMUM_NUMBER_OF_BEAMS_UNSPECIFIED | 0 |  |
| MAXIMUM_NUMBER_OF_BEAMS_MAX_128 | 1 | 128 beams |
| MAXIMUM_NUMBER_OF_BEAMS_MAX_256 | 2 | 256 beams |
| MAXIMUM_NUMBER_OF_BEAMS_MAX_512 | 3 | 512 beams |
| MAXIMUM_NUMBER_OF_BEAMS_MAX_1024 | 4 | 1024 beams |



<a name="blueye-protocol-MultibeamConfig-PingRate"></a>

### MultibeamConfig.PingRate


| Name | Number | Description |
| ---- | ------ | ----------- |
| PING_RATE_UNSPECIFIED | 0 |  |
| PING_RATE_NORMAL | 1 | 10Hz max ping rate |
| PING_RATE_HIGH | 2 | 15Hz max ping rate |
| PING_RATE_HIGHEST | 3 | 40Hz max ping rate |
| PING_RATE_LOW | 4 | 5Hz max ping rate |
| PING_RATE_LOWEST | 5 | 2Hz max ping rate |
| PING_RATE_STANDBY | 6 | Disable ping |



<a name="blueye-protocol-MultibeamFrequencyMode"></a>

### MultibeamFrequencyMode


| Name | Number | Description |
| ---- | ------ | ----------- |
| MULTIBEAM_FREQUENCY_MODE_UNSPECIFIED | 0 |  |
| MULTIBEAM_FREQUENCY_MODE_AUTO | 1 | Auto switching mode (if available) |
| MULTIBEAM_FREQUENCY_MODE_LOW_FREQUENCY | 2 | Low frequency mode (wide aperture, navigation) |
| MULTIBEAM_FREQUENCY_MODE_HIGH_FREQUENCY | 3 | High frequency mode (narrow aperture, target identification) |



<a name="blueye-protocol-NavigationSensorID"></a>

### NavigationSensorID
List of navigation sensors that can be used by the position observer

| Name | Number | Description |
| ---- | ------ | ----------- |
| NAVIGATION_SENSOR_ID_UNSPECIFIED | 0 | Unspecified |
| NAVIGATION_SENSOR_ID_WATERLINKED_DVL_A50 | 1 | Water Linked DVL A50 |
| NAVIGATION_SENSOR_ID_WATERLINKED_UGPS_G2 | 2 | Water Linked UGPS G2 |
| NAVIGATION_SENSOR_ID_NMEA | 3 | NMEA stream from external positioning system |
| NAVIGATION_SENSOR_ID_BLUEYE_GNSS | 4 | Blueye GNSS device on the ROV |
| NAVIGATION_SENSOR_ID_NORTEK_DVL_NUCLEUS | 5 | Nortek DVL Nucleus 1000 |



<a name="blueye-protocol-NotificationLevel"></a>

### NotificationLevel
List of available notification levels.

| Name | Number | Description |
| ---- | ------ | ----------- |
| NOTIFICATION_LEVEL_UNSPECIFIED | 0 | Unspecified |
| NOTIFICATION_LEVEL_INFO | 1 | Info |
| NOTIFICATION_LEVEL_WARNING | 2 | Warning |
| NOTIFICATION_LEVEL_ERROR | 3 | Error |



<a name="blueye-protocol-NotificationType"></a>

### NotificationType
Notification is used for displaying info, warnings, and errors to the user.

| Name | Number | Description |
| ---- | ------ | ----------- |
| NOTIFICATION_TYPE_UNSPECIFIED | 0 | Unspecified |
| NOTIFICATION_TYPE_POSITION_ESTIMATE_IS_INACCURATE | 1 | Position estimate is inaccurate |
| NOTIFICATION_TYPE_DRONE_POSITION_IS_UNKNOWN | 2 | Drone position is unknown |
| NOTIFICATION_TYPE_USER_POSITION_IS_UNKNOWN | 3 | User position is unknown |
| NOTIFICATION_TYPE_NO_MISSION_LOADED | 4 | No mission is loaded |
| NOTIFICATION_TYPE_MISSION_LOADED | 5 | Mission is loaded |
| NOTIFICATION_TYPE_FAILED_TO_LOAD_MISSION | 6 | Failed to load mission |
| NOTIFICATION_TYPE_MISSION_COMPLETE | 7 | Mission is complete |
| NOTIFICATION_TYPE_INSTRUCTION_COMPLETE | 8 | Instruction is complete |
| NOTIFICATION_TYPE_WAYPOINT_REACHED | 9 | Waypoint reached |
| NOTIFICATION_TYPE_DEPTH_TARGET_REACHED | 10 | Depth set point is reached |
| NOTIFICATION_TYPE_ALTITUDE_TARGET_REACHED | 11 | Altitude set point is reached |
| NOTIFICATION_TYPE_WAYPOINT_IS_TOO_FAR_AWAY | 12 | The waypoint is too far away |
| NOTIFICATION_TYPE_DEPTH_SET_POINT_IS_TOO_FAR_AWAY | 13 | The depth set point is too far away |
| NOTIFICATION_TYPE_TIME_TO_COMPLETE_IS_TOO_LONG | 14 | The time to complete the mission is too long |
| NOTIFICATION_TYPE_RETURNING_TO_HOME | 15 | Returning to home |
| NOTIFICATION_TYPE_GO_TO_SURFACE | 16 | Go to surface |
| NOTIFICATION_TYPE_GO_TO_SEABED | 17 | Go to seabed with an altimeter |
| NOTIFICATION_TYPE_GO_TO_WAYPOINT | 18 | Go to waypoint |
| NOTIFICATION_TYPE_GO_TO_DEPTH_SET_POINT | 19 | Go to depth set point |
| NOTIFICATION_TYPE_GO_TO_WAYPOINT_WITH_DEPTH_SET_POINT | 20 | Go to waypoint with depth set point |
| NOTIFICATION_TYPE_MISSION_STARTED | 21 | Mission is started |
| NOTIFICATION_TYPE_MISSION_PAUSED | 22 | Mission is paused |
| NOTIFICATION_TYPE_MISSION_RESUMED | 23 | Mission is resumed |
| NOTIFICATION_TYPE_MISSION_ABORTED | 24 | Mission is aborted |
| NOTIFICATION_TYPE_DRONE_IS_STUCK | 25 | Drone is stuck during a mission |
| NOTIFICATION_TYPE_WAIT_FOR | 26 | Wait for instruction running |
| NOTIFICATION_TYPE_CAMERA_ACTION | 27 | Camera action initiated |
| NOTIFICATION_TYPE_SET_TILT_MAIN_CAMERA | 28 | Set tilt for main camera |
| NOTIFICATION_TYPE_SET_TILT_MULTIBEAM | 29 | Set tilt for multibeam |
| NOTIFICATION_TYPE_INSTRUCTION_SKIPPED | 30 | When an instruction is not available in the ROV |
| NOTIFICATION_TYPE_DVL_HIGH_TEMPERATURE_DETECTED | 31 | DVL high temperature detected |
| NOTIFICATION_TYPE_DVL_THERMAL_PROTECTION_MODE_DETECTED | 32 | DVL thermal protection mode detected |



<a name="blueye-protocol-PingerConfiguration-MountingDirection"></a>

### PingerConfiguration.MountingDirection


| Name | Number | Description |
| ---- | ------ | ----------- |
| MOUNTING_DIRECTION_UNSPECIFIED | 0 | Mounting direction is unspecified |
| MOUNTING_DIRECTION_FORWARDS | 1 | Pointing forwards from the drones perspective |
| MOUNTING_DIRECTION_DOWNWARDS | 2 | Pointing downwards from the drones perspective |



<a name="blueye-protocol-PressureSensorType"></a>

### PressureSensorType
Depth sensors used by the drone.

| Name | Number | Description |
| ---- | ------ | ----------- |
| PRESSURE_SENSOR_TYPE_UNSPECIFIED | 0 | Depth sensor type not specified |
| PRESSURE_SENSOR_TYPE_NOT_CONNECTED | 1 | No se |
| PRESSURE_SENSOR_TYPE_MS5837_30BA26 | 2 | Thh MS5837 30BA26 pressure sensor |
| PRESSURE_SENSOR_TYPE_KELLER_PA7LD | 3 | The extended depth sensor using the Keller PA7LD pressure sensor |
| PRESSURE_SENSOR_TYPE_MS5637_02BA03 | 4 | The internal pressure sensor using the MS5637 02BA03 pressure sensor |



<a name="blueye-protocol-ResetCoordinateSource"></a>

### ResetCoordinateSource


| Name | Number | Description |
| ---- | ------ | ----------- |
| RESET_COORDINATE_SOURCE_UNSPECIFIED | 0 | Unspecified, fallback to device GPS |
| RESET_COORDINATE_SOURCE_DEVICE_GPS | 1 | Uses the device GPS to set the reset point |
| RESET_COORDINATE_SOURCE_MANUAL | 2 | Uses a coordinate in decimal degrees to set the reset point |



<a name="blueye-protocol-Resolution"></a>

### Resolution
Available camera resolutions.

| Name | Number | Description |
| ---- | ------ | ----------- |
| RESOLUTION_UNSPECIFIED | 0 | Resolution not specified |
| RESOLUTION_FULLHD_1080P | 1 | 1080p Full HD resolution |
| RESOLUTION_HD_720P | 2 | 720p HD resolution |



<a name="blueye-protocol-TemperatureUnit"></a>

### TemperatureUnit
Available temperature units.

| Name | Number | Description |
| ---- | ------ | ----------- |
| TEMPERATURE_UNIT_UNSPECIFIED | 0 | Temperature unit not specified |
| TEMPERATURE_UNIT_CELSIUS | 1 | Temperature should be displayed as Celsius |
| TEMPERATURE_UNIT_FAHRENHEIT | 2 | Temperature should be displayed as Fahrenheit |



<a name="blueye-protocol-ThicknessUnit"></a>

### ThicknessUnit
Available thickness units.

| Name | Number | Description |
| ---- | ------ | ----------- |
| THICKNESS_UNIT_UNSPECIFIED | 0 | Thickness unit not specified |
| THICKNESS_UNIT_MILLIMETERS | 1 | Thickness should be displayed as millimeters |
| THICKNESS_UNIT_INCHES | 2 | Thickness should be displayed as inches |




<a name="mission_planning-proto"></a>

## mission_planning.proto
Mission Planning Protocol

These messages are used to start a mission and to monitor the status of the mission.


<a name="blueye-protocol-CameraCommand"></a>

### CameraCommand
CameraCommands are used to control the camera from a mission.


| Field | Type | Description |
| ------| ---- | ----------- |
| camera_action | [ CameraAction](#blueye-protocol-CameraAction) | Camera command |
| action_param | [ float](#float) | Used for taking photos based on a time or distance interval |

<a name="blueye-protocol-ControlModeCommand"></a>

### ControlModeCommand
A ControlModeCommand is used to set vertical and horizontal control mode during a mission.


| Field | Type | Description |
| ------| ---- | ----------- |
| control_mode_vertical | [ ControlModeVertical](#blueye-protocol-ControlModeVertical) | Desired control mode in heave |
| control_mode_horizontal | [ ControlModeHorizontal](#blueye-protocol-ControlModeHorizontal) | Desired control mode in surge and yaw |

<a name="blueye-protocol-DepthSetPoint"></a>

### DepthSetPoint
Depth set point is used to describe a depth set-point relative to the surface or the seabed.


| Field | Type | Description |
| ------| ---- | ----------- |
| depth | [ float](#float) | Desired depth at the wp (m) |
| speed_to_depth | [ float](#float) | Desired speed to desired depth set point (m/s) |
| depth_zero_reference | [ DepthZeroReference](#blueye-protocol-DepthZeroReference) | Used to distinguish desired altitude or depth |

<a name="blueye-protocol-DepthSetPointCommand"></a>

### DepthSetPointCommand
A DepthSetPointCommand is used to go to a desired depth or altitude.


| Field | Type | Description |
| ------| ---- | ----------- |
| depth_set_point | [ DepthSetPoint](#blueye-protocol-DepthSetPoint) | Depth set point to go to |

<a name="blueye-protocol-GoToHomeCommand"></a>

### GoToHomeCommand
GoToHomeCommand is used to go to the home position.


| Field | Type | Description |
| ------| ---- | ----------- |
| desired_speed | [ float](#float) | Desired speed to home (m/s) |

<a name="blueye-protocol-GoToSeabedCommand"></a>

### GoToSeabedCommand
GoToSeabedCommand is used to go to the seabed.


| Field | Type | Description |
| ------| ---- | ----------- |
| desired_speed | [ float](#float) | Desired speed to seabed (m/s) |

<a name="blueye-protocol-GoToSurfaceCommand"></a>

### GoToSurfaceCommand
GoToSurfaceCommand is used to go to the surface.


| Field | Type | Description |
| ------| ---- | ----------- |
| desired_speed | [ float](#float) | Desired speed to surface (m/s) |

<a name="blueye-protocol-Instruction"></a>

### Instruction
A mission consists of one or multiple instructions. One instruction can be of different types.


| Field | Type | Description |
| ------| ---- | ----------- |
| id | [ uint32](#uint32) |  |
| group_id | [ uint32](#uint32) | Group id used for polygons |
| auto_continue | [ bool](#bool) | False will pause the mission after this instruction |
| <small><strong>oneof</strong> <code>command</code></small><br>waypoint_command | [ WaypointCommand](#blueye-protocol-WaypointCommand) | Go to waypoint |
| <small><strong>oneof</strong> <code>command</code></small><br>depth_set_point_command | [ DepthSetPointCommand](#blueye-protocol-DepthSetPointCommand) | Go to depth |
| <small><strong>oneof</strong> <code>command</code></small><br>camera_command | [ CameraCommand](#blueye-protocol-CameraCommand) | Camera commands |
| <small><strong>oneof</strong> <code>command</code></small><br>control_mode_command | [ ControlModeCommand](#blueye-protocol-ControlModeCommand) | Set control modes |
| <small><strong>oneof</strong> <code>command</code></small><br>tilt_main_camera_command | [ TiltMainCameraCommand](#blueye-protocol-TiltMainCameraCommand) | Set camera to angle x |
| <small><strong>oneof</strong> <code>command</code></small><br>tilt_multibeam_command | [ TiltMultibeamCommand](#blueye-protocol-TiltMultibeamCommand) | Set multibeam tilt angle |
| <small><strong>oneof</strong> <code>command</code></small><br>wait_for_command | [ WaitForCommand](#blueye-protocol-WaitForCommand) | Wait for x seconds |
| <small><strong>oneof</strong> <code>command</code></small><br>go_to_surface_command | [ GoToSurfaceCommand](#blueye-protocol-GoToSurfaceCommand) | Go to surface |
| <small><strong>oneof</strong> <code>command</code></small><br>go_to_seabed_command | [ GoToSeabedCommand](#blueye-protocol-GoToSeabedCommand) | Go to seabed |
| <small><strong>oneof</strong> <code>command</code></small><br>go_to_home_command | [ GoToHomeCommand](#blueye-protocol-GoToHomeCommand) | Go to home position |

<a name="blueye-protocol-Mission"></a>

### Mission
A list of waypoints describes a mission that the auto pilot can execute.


| Field | Type | Description |
| ------| ---- | ----------- |
| id | [ uint32](#uint32) | Mission id |
| name | [ string](#string) | Mission name provided from the app |
| instructions | [repeated Instruction](#blueye-protocol-Instruction) | List of instructions in the mission |
| path_segments | [repeated PathSegment](#blueye-protocol-PathSegment) | Calculated path segments from the reference generator (optional) |
| total_distance | [ uint32](#uint32) | Total distance of the mission (m) (optional) |
| total_duration_time | [ uint32](#uint32) | Total duration time of the mission (s) (optional) |
| default_surge_speed | [ float](#float) | Default cruise speed of the mission (m/s) (optional) |
| default_heave_speed | [ float](#float) | Default heave speed of the mission (m/s) (optional) |
| default_circle_of_acceptance | [ float](#float) | Default circle of acceptance for waypoints (m) (optional) |

<a name="blueye-protocol-MissionStatus"></a>

### MissionStatus
Mission Status is used for showing the status of the mission.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ MissionState](#blueye-protocol-MissionState) | State of the mission supervisor |
| time_elapsed | [ uint32](#uint32) | Time elapsed since mission started (s) |
| estimated_time_to_complete | [ uint32](#uint32) | Estimated time to complete the mission (s) |
| distance_to_complete | [ uint32](#uint32) | Distance left of the mission (m) |
| completed_instruction_ids | [repeated uint32](#uint32) | Ids of the completed instructions |
| total_number_of_instructions | [ uint32](#uint32) | Total number of instructions in the mission |
| completed_path_segment_ids | [repeated uint32](#uint32) | Ids of the completed path segments |
| total_number_of_path_segments | [ uint32](#uint32) | Total number of path segments in the mission |
| id | [ uint32](#uint32) | Mission id of the active mission |

<a name="blueye-protocol-PathSegment"></a>

### PathSegment
Path segment used to describe segments of a mission as a line between to waypoints.


| Field | Type | Description |
| ------| ---- | ----------- |
| id | [ uint32](#uint32) | Path segment id starting at 0, -1 for inactive |
| speed_to_target | [ float](#float) | Desired speed over ground in (m/s) |
| course_to_target | [ float](#float) | Course to target relative to north (rad) [-pi, pi] |
| depth_speed | [ float](#float) | Desired speed in heave (m/s) |
| horizontal_length | [ float](#float) | Horizontal length of the path segment (m) |
| vertical_length | [ float](#float) | Vertical length of the path segment (m) |
| from_wp_id | [ uint32](#uint32) | Id of the starting waypoint |
| to_wp_id | [ uint32](#uint32) | Id of the ending waypoint |
| duration_time | [ float](#float) | Estimated time it takes to complete given length and desired speed (s) |

<a name="blueye-protocol-ReferenceAutoPilot"></a>

### ReferenceAutoPilot
Reference for the auto pilot when a mission is active.


| Field | Type | Description |
| ------| ---- | ----------- |
| instruction_type | [ InstructionType](#blueye-protocol-InstructionType) | Instruction type |
| active_instruction_id | [ uint32](#uint32) | Id of the active instruction |
| active_path_segment_id | [ uint32](#uint32) | Id of the active path segment |
| course_to_target | [ float](#float) | Course to the next waypoint from north (rad) [-pi, pi] |
| speed_over_ground | [ float](#float) | Desired speed over ground (m/s) |
| horizontal_distance_to_target | [ float](#float) | Horizontal distance to the next waypoint (m) |
| circle_of_acceptance | [ float](#float) | Circle of acceptance to mark waypoint as visited (m) |
| depth_set_point | [ float](#float) | Desired depth set point (m) |
| heave_velocity | [ float](#float) | Desired heave velocity (m/s) |
| vertical_distance_to_target | [ float](#float) | Vertical distance to the next waypoint (m) |
| depth_zero_reference | [ DepthZeroReference](#blueye-protocol-DepthZeroReference) | Indicates if depth is measured from the surface or seabed |
| time_to_complete | [ float](#float) | Estimated time to complete the instruction (s) |

<a name="blueye-protocol-TiltMainCameraCommand"></a>

### TiltMainCameraCommand
The TiltMainCameraCommand can set the desired camera tilt angle.


| Field | Type | Description |
| ------| ---- | ----------- |
| tilt_angle | [ TiltAngle](#blueye-protocol-TiltAngle) | Tilt angle of the camera (-30..30) |

<a name="blueye-protocol-TiltMultibeamCommand"></a>

### TiltMultibeamCommand
The TiltMultibeamCommand is used to set the tilt angle of the servo.


| Field | Type | Description |
| ------| ---- | ----------- |
| multibeam_servo | [ MultibeamServo](#blueye-protocol-MultibeamServo) | Tilt angle for the multibeam servo |

<a name="blueye-protocol-WaitForCommand"></a>

### WaitForCommand
WaitForCommand is used to wait during a mission.


| Field | Type | Description |
| ------| ---- | ----------- |
| wait_for_seconds | [ float](#float) | Wait for x seconds |

<a name="blueye-protocol-Waypoint"></a>

### Waypoint
Waypoints used to describe a path for the auto pilot.


| Field | Type | Description |
| ------| ---- | ----------- |
| id | [ uint32](#uint32) | Waypoint id |
| name | [ string](#string) | Waypoint name provided from the app |
| global_position | [ LatLongPosition](#blueye-protocol-LatLongPosition) | Position if the waypoint (decimal degrees) |
| circle_of_acceptance | [ float](#float) | Radius of the acceptance circle around the waypoint (m) |
| speed_to_target | [ float](#float) | Desired speed over ground to waypoint (m/s) |
| depth_set_point | [ DepthSetPoint](#blueye-protocol-DepthSetPoint) | Depth set point (optional) |

<a name="blueye-protocol-WaypointCommand"></a>

### WaypointCommand
A WaypointCommand will request the drone to drive to a point automatically.


| Field | Type | Description |
| ------| ---- | ----------- |
| waypoint | [ Waypoint](#blueye-protocol-Waypoint) | Waypoint to go to |



<a name="blueye-protocol-CameraAction"></a>

### CameraAction
List of available camera actions.

| Name | Number | Description |
| ---- | ------ | ----------- |
| CAMERA_ACTION_UNSPECIFIED | 0 | Unspecified command |
| CAMERA_ACTION_TAKE_PHOTO | 1 | Take one photo |
| CAMERA_ACTION_TAKE_PHOTOS_TIME | 2 | Take a photo every x second |
| CAMERA_ACTION_TAKE_PHOTOS_DISTANCE | 3 | Take a photo every x meter |
| CAMERA_ACTION_STOP_TAKING_PHOTOS | 4 | Stop taking photos |
| CAMERA_ACTION_START_RECORDING | 5 | Start recording |
| CAMERA_ACTION_STOP_RECORDING | 6 | Stop recording |



<a name="blueye-protocol-ControlModeHorizontal"></a>

### ControlModeHorizontal


| Name | Number | Description |
| ---- | ------ | ----------- |
| CONTROL_MODE_HORIZONTAL_UNSPECIFIED | 0 | Unspecified |
| CONTROL_MODE_HORIZONTAL_MANUAL | 1 | Manual control mode |
| CONTROL_MODE_HORIZONTAL_AUTO_HEADING | 2 | Auto heading control mode |
| CONTROL_MODE_HORIZONTAL_STATION_KEEPING | 3 | Station keeping control mode |



<a name="blueye-protocol-ControlModeVertical"></a>

### ControlModeVertical


| Name | Number | Description |
| ---- | ------ | ----------- |
| CONTROL_MODE_VERTICAL_UNSPECIFIED | 0 | Unspecified |
| CONTROL_MODE_VERTICAL_MANUAL | 1 | Manual control mode |
| CONTROL_MODE_VERTICAL_AUTO_DEPTH | 2 | Auto depth control mode |
| CONTROL_MODE_VERTICAL_AUTO_ALTITUDE | 3 | Auto altitude control mode |



<a name="blueye-protocol-DepthZeroReference"></a>

### DepthZeroReference
Depth zero reference from surface for depth, and seabed for altitude.

| Name | Number | Description |
| ---- | ------ | ----------- |
| DEPTH_ZERO_REFERENCE_UNSPECIFIED | 0 |  |
| DEPTH_ZERO_REFERENCE_SURFACE | 1 |  |
| DEPTH_ZERO_REFERENCE_SEABED | 2 |  |



<a name="blueye-protocol-InstructionType"></a>

### InstructionType
List of available instruction types.

| Name | Number | Description |
| ---- | ------ | ----------- |
| INSTRUCTION_TYPE_UNSPECIFIED | 0 | Unspecified |
| INSTRUCTION_TYPE_NONE | 1 | None |
| INSTRUCTION_TYPE_GO_TO_WAYPOINT | 2 | Go to waypoint |
| INSTRUCTION_TYPE_GO_TO_WAYPOINT_WITH_DEPTH_SET_POINT | 3 | Go to waypoint with depth set point |
| INSTRUCTION_TYPE_GO_TO_DEPTH_SET_POINT | 4 | Go to depth set point |
| INSTRUCTION_TYPE_SET_CAMERA_ACTION | 5 | Command used to take photo repeatedly or start, stop recording |
| INSTRUCTION_TYPE_SET_CONTROL_MODE | 6 | Sets a new control mode |
| INSTRUCTION_TYPE_SET_TILT_MAIN_CAMERA | 7 | Sets a new angle for the tilt servo |
| INSTRUCTION_TYPE_SET_TILT_SERVO | 8 | Sets a new angle for the tilt servo |
| INSTRUCTION_TYPE_WAIT_FOR_SEC | 9 | Waiting for requested time in seconds |
| INSTRUCTION_TYPE_GO_TO_SURFACE | 10 | Go to the surface |
| INSTRUCTION_TYPE_GO_TO_SEABED | 11 | Go to the seabed |
| INSTRUCTION_TYPE_GO_TO_HOME | 12 | Returning to home |



<a name="blueye-protocol-MissionState"></a>

### MissionState
List of mission supervisor states.

| Name | Number | Description |
| ---- | ------ | ----------- |
| MISSION_STATE_UNSPECIFIED | 0 | Unspecified |
| MISSION_STATE_INACTIVE | 1 | Mission supervisor is inactive |
| MISSION_STATE_READY | 2 | Ready to start mission |
| MISSION_STATE_RUNNING | 3 | Mission is running |
| MISSION_STATE_PAUSED | 4 | Mission is paused |
| MISSION_STATE_COMPLETED | 5 | Mission is completed |
| MISSION_STATE_ABORTED | 6 | Mission is aborted by the mission supervisor |
| MISSION_STATE_FAILED_TO_LOAD_MISSION | 7 | Mission has failed to load |
| MISSION_STATE_FAILED_TO_START_MISSION | 8 | Mission has failed to start |




<a name="req_rep-proto"></a>

## req_rep.proto
Request reply

These messages define request / reply messages for the Blueye drone.


<a name="blueye-protocol-ConnectClientRep"></a>

### ConnectClientRep
Response after connecting a client to the drone.

Contains information about which client is in control, and a list of
all connected clients.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_id | [ uint32](#uint32) | The assigned ID of this client. |
| client_id_in_control | [ uint32](#uint32) | The ID of the client in control of the drone. |
| connected_clients | [repeated ConnectedClient](#blueye-protocol-ConnectedClient) | List of connected clients. |

<a name="blueye-protocol-ConnectClientReq"></a>

### ConnectClientReq
Connect a new client to the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_info | [ ClientInfo](#blueye-protocol-ClientInfo) | Information about the client connecting to the drone. |

<a name="blueye-protocol-DisconnectClientRep"></a>

### DisconnectClientRep
Response after disconnecting a client from the drone.

Contains information about which clients are connected and in control.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_id_in_control | [ uint32](#uint32) | The ID of the client in control of the drone. |
| connected_clients | [repeated ConnectedClient](#blueye-protocol-ConnectedClient) | List of connected clients. |

<a name="blueye-protocol-DisconnectClientReq"></a>

### DisconnectClientReq
Disconnect a client from the drone.

This request will remove the client from the list of connected clients.
It allows clients to disconnect instantly, without waiting for a watchdog to
clear the client in control, or promote a new client to be in control.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_id | [ uint32](#uint32) | The assigned ID of the client to disconnect. |

<a name="blueye-protocol-GetBatteryRep"></a>

### GetBatteryRep
Response with essential battery information.


| Field | Type | Description |
| ------| ---- | ----------- |
| battery | [ Battery](#blueye-protocol-Battery) | Essential battery information. |

<a name="blueye-protocol-GetBatteryReq"></a>

### GetBatteryReq
Request essential battery information.

Can be used to instantly get battery information,
instead of having to wait for the BatteryTel message to be received.


<a name="blueye-protocol-GetCameraParametersRep"></a>

### GetCameraParametersRep
Response with the currently set camera parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| camera_parameters | [ CameraParameters](#blueye-protocol-CameraParameters) | The currently set camera parameters. |

<a name="blueye-protocol-GetCameraParametersReq"></a>

### GetCameraParametersReq
Request to get the currently set camera parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| camera | [ Camera](#blueye-protocol-Camera) | Which camera to read camera parameters from. |

<a name="blueye-protocol-GetMissionRep"></a>

### GetMissionRep
Get active mission response.


| Field | Type | Description |
| ------| ---- | ----------- |
| mission | [ Mission](#blueye-protocol-Mission) | active mission with waypoints |

<a name="blueye-protocol-GetMissionReq"></a>

### GetMissionReq
Service request to the reference_generator to get the active mission.


<a name="blueye-protocol-GetOverlayParametersRep"></a>

### GetOverlayParametersRep
Response with the currently set video overlay parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| overlay_parameters | [ OverlayParameters](#blueye-protocol-OverlayParameters) | The currently set overlay parameters. |

<a name="blueye-protocol-GetOverlayParametersReq"></a>

### GetOverlayParametersReq
Request to get currently set video overlay parameters.


<a name="blueye-protocol-GetPersistentStorageSettingsRep"></a>

### GetPersistentStorageSettingsRep
Response with the currently set persistent storage settings.


| Field | Type | Description |
| ------| ---- | ----------- |
| persistent_storage_settings | [ PersistentStorageSettings](#blueye-protocol-PersistentStorageSettings) | The currently set persistent storage settings. |

<a name="blueye-protocol-GetPersistentStorageSettingsReq"></a>

### GetPersistentStorageSettingsReq
Request to get currently set persistent storage settings.


<a name="blueye-protocol-GetTelemetryRep"></a>

### GetTelemetryRep
Response with latest telemetry


| Field | Type | Description |
| ------| ---- | ----------- |
| payload | [ google.protobuf.Any](#google-protobuf-Any) | The latest telemetry data, empty if no data available. |

<a name="blueye-protocol-GetTelemetryReq"></a>

### GetTelemetryReq
Request to get latest telemetry data


| Field | Type | Description |
| ------| ---- | ----------- |
| message_type | [ string](#string) | Message name, f. ex. "AttitudeTel" |

<a name="blueye-protocol-PingRep"></a>

### PingRep
Response message from a PingReq request.


<a name="blueye-protocol-PingReq"></a>

### PingReq
The simplest message to use to test request/reply communication with the drone.

The drone replies with a PingRep message immediately after receiving the PingReq.


<a name="blueye-protocol-SetCameraParametersRep"></a>

### SetCameraParametersRep
Response after setting the camera parameters.


<a name="blueye-protocol-SetCameraParametersReq"></a>

### SetCameraParametersReq
Request to set camera parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| camera_parameters | [ CameraParameters](#blueye-protocol-CameraParameters) | The camera parameters to apply. |

<a name="blueye-protocol-SetInstructionUpdateRep"></a>

### SetInstructionUpdateRep
Response after updating an instruction in the current mission.


<a name="blueye-protocol-SetInstructionUpdateReq"></a>

### SetInstructionUpdateReq
Updates an instruction in current mission with a new instruction payload.


| Field | Type | Description |
| ------| ---- | ----------- |
| instruction | [ Instruction](#blueye-protocol-Instruction) | instruction that will replace the desired instruction |

<a name="blueye-protocol-SetMissionRep"></a>

### SetMissionRep
Response after setting a new mission.


<a name="blueye-protocol-SetMissionReq"></a>

### SetMissionReq
Issue a desired mission to the reference_generator.


| Field | Type | Description |
| ------| ---- | ----------- |
| mission | [ Mission](#blueye-protocol-Mission) | requested mission issued to the reference generator |

<a name="blueye-protocol-SetOverlayParametersRep"></a>

### SetOverlayParametersRep
Response after setting video overlay parameters.


<a name="blueye-protocol-SetOverlayParametersReq"></a>

### SetOverlayParametersReq
Request to set video overlay parameters.


| Field | Type | Description |
| ------| ---- | ----------- |
| overlay_parameters | [ OverlayParameters](#blueye-protocol-OverlayParameters) | The video overlay parameters to apply. |

<a name="blueye-protocol-SetPersistentStorageSettingsRep"></a>

### SetPersistentStorageSettingsRep
Response after setting persistent storage settings.


| Field | Type | Description |
| ------| ---- | ----------- |
| success | [ bool](#bool) | If the persistent storage settings were set successfully. |

<a name="blueye-protocol-SetPersistentStorageSettingsReq"></a>

### SetPersistentStorageSettingsReq
Request to set persistent storage settings.


| Field | Type | Description |
| ------| ---- | ----------- |
| persistent_storage_settings | [ PersistentStorageSettings](#blueye-protocol-PersistentStorageSettings) | The persistent storage settings to apply. |

<a name="blueye-protocol-SetPubFrequencyRep"></a>

### SetPubFrequencyRep
Response after updating publish frequency


| Field | Type | Description |
| ------| ---- | ----------- |
| success | [ bool](#bool) | True if message name valid and frequency successfully updated. |

<a name="blueye-protocol-SetPubFrequencyReq"></a>

### SetPubFrequencyReq
Request to update the publish frequency


| Field | Type | Description |
| ------| ---- | ----------- |
| message_type | [ string](#string) | Message name, f. ex. "AttitudeTel" |
| frequency | [ float](#float) | Publish frequency (max 100 Hz). |

<a name="blueye-protocol-SetThicknessGaugeParametersRep"></a>

### SetThicknessGaugeParametersRep
Response after setting thickness gauge parameters.


<a name="blueye-protocol-SetThicknessGaugeParametersReq"></a>

### SetThicknessGaugeParametersReq
Request to set parameters for ultrasonic thickness gauge.

The sound velocity is used to calculate the thickness of the material being measured.


| Field | Type | Description |
| ------| ---- | ----------- |
| sound_velocity | [ uint32](#uint32) | Sound velocity in m/s |

<a name="blueye-protocol-SyncTimeRep"></a>

### SyncTimeRep
Response after setting the system time on the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| success | [ bool](#bool) | If the time was set successfully. |

<a name="blueye-protocol-SyncTimeReq"></a>

### SyncTimeReq
Request to set the system time on the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| time | [ SystemTime](#blueye-protocol-SystemTime) | The time to set on the drone. |




<a name="telemetry-proto"></a>

## telemetry.proto
Telemetry

These messages define telemetry messages from the Blueye drone.


<a name="blueye-protocol-AltitudeTel"></a>

### AltitudeTel
Receive the current altitude of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| altitude | [ Altitude](#blueye-protocol-Altitude) | The altitude of the drone. |

<a name="blueye-protocol-AquaTrollProbeMetadataTel"></a>

### AquaTrollProbeMetadataTel
Metadata from the In-Situ Aqua Troll probe's common registers


| Field | Type | Description |
| ------| ---- | ----------- |
| probe | [ AquaTrollProbeMetadata](#blueye-protocol-AquaTrollProbeMetadata) | AquaTroll message containing sensor array. |

<a name="blueye-protocol-AquaTrollSensorMetadataTel"></a>

### AquaTrollSensorMetadataTel
Metadata from a single sensor from In-Situ Aqua Troll probe


| Field | Type | Description |
| ------| ---- | ----------- |
| sensors | [ AquaTrollSensorMetadataArray](#blueye-protocol-AquaTrollSensorMetadataArray) | AquaTroll message containing sensor array. |

<a name="blueye-protocol-AquaTrollSensorParametersTel"></a>

### AquaTrollSensorParametersTel
Single sensor from In-Situ Aqua Troll probe


| Field | Type | Description |
| ------| ---- | ----------- |
| sensors | [ AquaTrollSensorParametersArray](#blueye-protocol-AquaTrollSensorParametersArray) | AquaTroll message containing parameter array. |

<a name="blueye-protocol-AttitudeTel"></a>

### AttitudeTel
Receive the current attitude of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| attitude | [ Attitude](#blueye-protocol-Attitude) | The attitude of the drone. |

<a name="blueye-protocol-BatteryBQ40Z50Tel"></a>

### BatteryBQ40Z50Tel
Receive detailed information about a battery using the
BQ40Z50 battery management system.


| Field | Type | Description |
| ------| ---- | ----------- |
| battery | [ BatteryBQ40Z50](#blueye-protocol-BatteryBQ40Z50) | Detailed battery information. |

<a name="blueye-protocol-BatteryTel"></a>

### BatteryTel
Receive essential information about the battery status.


| Field | Type | Description |
| ------| ---- | ----------- |
| battery | [ Battery](#blueye-protocol-Battery) | Essential battery information. |

<a name="blueye-protocol-CPUInfoTel"></a>

### CPUInfoTel
Information about cpu and memory usage


| Field | Type | Description |
| ------| ---- | ----------- |
| cpu_info | [ CPUInfo](#blueye-protocol-CPUInfo) |  |

<a name="blueye-protocol-CPUTemperatureTel"></a>

### CPUTemperatureTel
Drone CPU temperature


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature | [ CPUTemperature](#blueye-protocol-CPUTemperature) |  |

<a name="blueye-protocol-CalibratedImuTel"></a>

### CalibratedImuTel
Calibrated IMU data


| Field | Type | Description |
| ------| ---- | ----------- |
| imu | [ Imu](#blueye-protocol-Imu) |  |

<a name="blueye-protocol-CalibrationStateTel"></a>

### CalibrationStateTel
Calibration state used for calibration routine.


| Field | Type | Description |
| ------| ---- | ----------- |
| calibration_state | [ CalibrationState](#blueye-protocol-CalibrationState) |  |

<a name="blueye-protocol-CanisterBottomHumidityTel"></a>

### CanisterBottomHumidityTel
Receive humidity information from the bottom canister.


| Field | Type | Description |
| ------| ---- | ----------- |
| humidity | [ CanisterHumidity](#blueye-protocol-CanisterHumidity) | Humidity information |

<a name="blueye-protocol-CanisterBottomTemperatureTel"></a>

### CanisterBottomTemperatureTel
Receive temperature information from the bottom canister.


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature | [ CanisterTemperature](#blueye-protocol-CanisterTemperature) | Temperature information. |

<a name="blueye-protocol-CanisterTopHumidityTel"></a>

### CanisterTopHumidityTel
Receive humidity information from the top canister.


| Field | Type | Description |
| ------| ---- | ----------- |
| humidity | [ CanisterHumidity](#blueye-protocol-CanisterHumidity) | Humidity information |

<a name="blueye-protocol-CanisterTopTemperatureTel"></a>

### CanisterTopTemperatureTel
Receive temperature information from the top canister.


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature | [ CanisterTemperature](#blueye-protocol-CanisterTemperature) | Temperature information. |

<a name="blueye-protocol-ConnectedClientsTel"></a>

### ConnectedClientsTel
List of connected clients telemetry message.


| Field | Type | Description |
| ------| ---- | ----------- |
| client_id_in_control | [ uint32](#uint32) | The client id of the client in control. |
| connected_clients | [repeated ConnectedClient](#blueye-protocol-ConnectedClient) | List of connected clients. |

<a name="blueye-protocol-ControlForceTel"></a>

### ControlForceTel
Control force in all directions.


| Field | Type | Description |
| ------| ---- | ----------- |
| control_force | [ ControlForce](#blueye-protocol-ControlForce) |  |

<a name="blueye-protocol-ControlModeTel"></a>

### ControlModeTel
Receive the current state of the control system.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ ControlMode](#blueye-protocol-ControlMode) | State of the control system. |

<a name="blueye-protocol-ControllerHealthTel"></a>

### ControllerHealthTel
Controller health indicating the load of the controller, used to set a color in the heading and depth bar.


| Field | Type | Description |
| ------| ---- | ----------- |
| controller_health | [ ControllerHealth](#blueye-protocol-ControllerHealth) |  |

<a name="blueye-protocol-CpProbeTel"></a>

### CpProbeTel
Cathodic Protection Potential probe telemetry message


| Field | Type | Description |
| ------| ---- | ----------- |
| cp_probe | [ CpProbe](#blueye-protocol-CpProbe) | Reading from cp probe. |

<a name="blueye-protocol-DataStorageSpaceTel"></a>

### DataStorageSpaceTel
Data storage info.


| Field | Type | Description |
| ------| ---- | ----------- |
| storage_space | [ StorageSpace](#blueye-protocol-StorageSpace) |  |

<a name="blueye-protocol-DepthTel"></a>

### DepthTel
Measurement of the drones position relative to the sea surface.


| Field | Type | Description |
| ------| ---- | ----------- |
| depth | [ Depth](#blueye-protocol-Depth) |  |

<a name="blueye-protocol-DiveTimeTel"></a>

### DiveTimeTel
Receive the dive time of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| dive_time | [ DiveTime](#blueye-protocol-DiveTime) | The current dive time of the drone. |

<a name="blueye-protocol-DroneInfoTel"></a>

### DroneInfoTel
Receive metadata and information about the connected drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| drone_info | [ DroneInfo](#blueye-protocol-DroneInfo) | Various metadata such as software versions and serial number. |

<a name="blueye-protocol-DroneTimeTel"></a>

### DroneTimeTel
Receive time information from the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| real_time_clock | [ SystemTime](#blueye-protocol-SystemTime) | The real-time clock of the drone. |
| monotonic_clock | [ SystemTime](#blueye-protocol-SystemTime) | The monotonic clock of the drone (time since power on). |

<a name="blueye-protocol-DvlVelocityTel"></a>

### DvlVelocityTel
Dvl raw sensor data.


| Field | Type | Description |
| ------| ---- | ----------- |
| dvl_velocity | [ DvlVelocity](#blueye-protocol-DvlVelocity) | Dvl velocity data. |

<a name="blueye-protocol-ErrorFlagsTel"></a>

### ErrorFlagsTel
Receive currently set error flags.


| Field | Type | Description |
| ------| ---- | ----------- |
| error_flags | [ ErrorFlags](#blueye-protocol-ErrorFlags) | Currently set error flags on the drone. |

<a name="blueye-protocol-ForwardDistanceTel"></a>

### ForwardDistanceTel
Distance to an object in front of the drone when a 1D pinger is mounted forwards.


| Field | Type | Description |
| ------| ---- | ----------- |
| forward_distance | [ ForwardDistance](#blueye-protocol-ForwardDistance) |  |

<a name="blueye-protocol-GenericServoTel"></a>

### GenericServoTel
State of a generic servo


| Field | Type | Description |
| ------| ---- | ----------- |
| servo | [ GenericServo](#blueye-protocol-GenericServo) | Servo state |

<a name="blueye-protocol-GuestPortCurrentTel"></a>

### GuestPortCurrentTel
GuestPort current readings


| Field | Type | Description |
| ------| ---- | ----------- |
| current | [ GuestPortCurrent](#blueye-protocol-GuestPortCurrent) |  |

<a name="blueye-protocol-GuestPortLightsTel"></a>

### GuestPortLightsTel
Receive the status of any guest port lights connected to the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| lights | [ Lights](#blueye-protocol-Lights) |  |

<a name="blueye-protocol-Imu1Tel"></a>

### Imu1Tel
Raw IMU data from IMU 1


| Field | Type | Description |
| ------| ---- | ----------- |
| imu | [ Imu](#blueye-protocol-Imu) |  |

<a name="blueye-protocol-Imu2Tel"></a>

### Imu2Tel
Raw IMU data from IMU 2


| Field | Type | Description |
| ------| ---- | ----------- |
| imu | [ Imu](#blueye-protocol-Imu) |  |

<a name="blueye-protocol-IperfTel"></a>

### IperfTel
Iperf indicates the available bandwidth on the tether from drone to surface unit.


| Field | Type | Description |
| ------| ---- | ----------- |
| status | [ IperfStatus](#blueye-protocol-IperfStatus) |  |

<a name="blueye-protocol-LaserTel"></a>

### LaserTel
Receive the status of any lasers connected to the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| laser | [ Laser](#blueye-protocol-Laser) |  |

<a name="blueye-protocol-LightsTel"></a>

### LightsTel
Receive the status of the main lights of the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| lights | [ Lights](#blueye-protocol-Lights) |  |

<a name="blueye-protocol-MedusaSpectrometerDataTel"></a>

### MedusaSpectrometerDataTel
Medusa gamma ray sensor spectrometer data


| Field | Type | Description |
| ------| ---- | ----------- |
| data | [ MedusaSpectrometerData](#blueye-protocol-MedusaSpectrometerData) |  |

<a name="blueye-protocol-MissionStatusTel"></a>

### MissionStatusTel
Mission status from the mission supervisor.


| Field | Type | Description |
| ------| ---- | ----------- |
| mission_status | [ MissionStatus](#blueye-protocol-MissionStatus) |  |

<a name="blueye-protocol-MultibeamConfigTel"></a>

### MultibeamConfigTel
Multibeam sonar config


| Field | Type | Description |
| ------| ---- | ----------- |
| config | [ MultibeamConfig](#blueye-protocol-MultibeamConfig) | Config data from a multibeam sonar |

<a name="blueye-protocol-MultibeamDiscoveryTel"></a>

### MultibeamDiscoveryTel
Multibeam sonar status message


| Field | Type | Description |
| ------| ---- | ----------- |
| discovery | [ MultibeamDiscovery](#blueye-protocol-MultibeamDiscovery) | Discovery data from a multibeam sonar |

<a name="blueye-protocol-MultibeamPingTel"></a>

### MultibeamPingTel
Multibeam sonar ping data


| Field | Type | Description |
| ------| ---- | ----------- |
| ping | [ MultibeamPing](#blueye-protocol-MultibeamPing) | Ping data from a multibeam sonar |

<a name="blueye-protocol-MultibeamServoTel"></a>

### MultibeamServoTel
State of the servo installed in the multibeam


| Field | Type | Description |
| ------| ---- | ----------- |
| servo | [ MultibeamServo](#blueye-protocol-MultibeamServo) | Multibeam servo state |

<a name="blueye-protocol-NStreamersTel"></a>

### NStreamersTel
Number of connected clients streaming video.


| Field | Type | Description |
| ------| ---- | ----------- |
| n_streamers | [ NStreamers](#blueye-protocol-NStreamers) |  |

<a name="blueye-protocol-NotificationTel"></a>

### NotificationTel
Notification from the control system.


| Field | Type | Description |
| ------| ---- | ----------- |
| notification | [ Notification](#blueye-protocol-Notification) |  |

<a name="blueye-protocol-PilotGPSPositionTel"></a>

### PilotGPSPositionTel
Pilot position (originating from device GPS) for logging.


| Field | Type | Description |
| ------| ---- | ----------- |
| position | [ LatLongPosition](#blueye-protocol-LatLongPosition) |  |

<a name="blueye-protocol-PositionEstimateTel"></a>

### PositionEstimateTel
Position estimate of the drone if a DVL or a positioning system is available.


| Field | Type | Description |
| ------| ---- | ----------- |
| position_estimate | [ PositionEstimate](#blueye-protocol-PositionEstimate) |  |

<a name="blueye-protocol-RecordStateTel"></a>

### RecordStateTel
Record state from the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| record_state | [ RecordState](#blueye-protocol-RecordState) |  |

<a name="blueye-protocol-ReferenceAutoPilotTel"></a>

### ReferenceAutoPilotTel
Reference for the auto pilot when a mission is active.


| Field | Type | Description |
| ------| ---- | ----------- |
| reference_auto_pilot | [ ReferenceAutoPilot](#blueye-protocol-ReferenceAutoPilot) |  |

<a name="blueye-protocol-ReferenceTel"></a>

### ReferenceTel
Reference signals indicating desired states.


| Field | Type | Description |
| ------| ---- | ----------- |
| reference | [ Reference](#blueye-protocol-Reference) |  |

<a name="blueye-protocol-ThicknessGaugeTel"></a>

### ThicknessGaugeTel
Thickness gauge measurement telemetry message.


| Field | Type | Description |
| ------| ---- | ----------- |
| thickness_gauge | [ ThicknessGauge](#blueye-protocol-ThicknessGauge) | Thickness measurement with a cygnus gauge. |

<a name="blueye-protocol-TiltAngleTel"></a>

### TiltAngleTel
Tilt angle state on main camera.


| Field | Type | Description |
| ------| ---- | ----------- |
| angle | [ TiltAngle](#blueye-protocol-TiltAngle) |  |

<a name="blueye-protocol-TiltStabilizationTel"></a>

### TiltStabilizationTel
Tilt stabilization state.


| Field | Type | Description |
| ------| ---- | ----------- |
| state | [ TiltStabilizationState](#blueye-protocol-TiltStabilizationState) |  |

<a name="blueye-protocol-TimeLapseStateTel"></a>

### TimeLapseStateTel
Time-lapse state from the drone.


| Field | Type | Description |
| ------| ---- | ----------- |
| time_lapse_state | [ TimeLapseState](#blueye-protocol-TimeLapseState) |  |

<a name="blueye-protocol-VideoStorageSpaceTel"></a>

### VideoStorageSpaceTel
Video storage info.


| Field | Type | Description |
| ------| ---- | ----------- |
| storage_space | [ StorageSpace](#blueye-protocol-StorageSpace) |  |

<a name="blueye-protocol-WaterTemperatureTel"></a>

### WaterTemperatureTel
Water temperature from the depth sensor.


| Field | Type | Description |
| ------| ---- | ----------- |
| temperature | [ WaterTemperature](#blueye-protocol-WaterTemperature) |  |




## Scalar Value Types

| .proto Type | Notes | C++ | Java | Python | Go | C# | PHP | Ruby |
| ----------- | ----- | --- | ---- | ------ | -- | -- | --- | ---- |
| <a name="double" /> double |  | double | double | float | float64 | double | float | Float |
| <a name="float" /> float |  | float | float | float | float32 | float | float | Float |
| <a name="int32" /> int32 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="int64" /> int64 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="uint32" /> uint32 | Uses variable-length encoding. | uint32 | int | int/long | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="uint64" /> uint64 | Uses variable-length encoding. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum or Fixnum (as required) |
| <a name="sint32" /> sint32 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sint64" /> sint64 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="fixed32" /> fixed32 | Always four bytes. More efficient than uint32 if values are often greater than 2^28. | uint32 | int | int | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="fixed64" /> fixed64 | Always eight bytes. More efficient than uint64 if values are often greater than 2^56. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum |
| <a name="sfixed32" /> sfixed32 | Always four bytes. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sfixed64" /> sfixed64 | Always eight bytes. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="bool" /> bool |  | bool | boolean | boolean | bool | bool | boolean | TrueClass/FalseClass |
| <a name="string" /> string | A string must always contain UTF-8 encoded or 7-bit ASCII text. | string | String | str/unicode | string | string | string | String (UTF-8) |
| <a name="bytes" /> bytes | May contain any arbitrary sequence of bytes. | string | ByteString | str | []byte | ByteString | string | String (ASCII-8BIT) |

