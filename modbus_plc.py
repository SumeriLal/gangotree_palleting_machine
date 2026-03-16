# -*- coding: UTF-8 -*-
# Import modules & global variables
if True:  # Convenient code folding, can be omitted
    import log, utime, _thread, checkNet, ujson
    from machine import WDT, UART
    import ubinascii as binascii
    import ustruct
    import math

    log.basicConfig(level=log.NOTSET)  # Set the log output level
    Grey_log = log.getLogger("Modbus-RS485")

    # Modbus-RS485 Setting Parameters
    _uartport = UART.UART2  # uart
    _baudrate = 9600  # Baud rate
    _databits = 8  # Data bit
    _parity = 0  # verify
    _stopbit = 1  # Stop bit
    _flowctl = 0  # Fluid control
    _control_485 = UART.GPIO3  # 485 Switch pin
    _device_address = 0x01  # Device address

    # 功能码(Function code)
    READ_COILS = 0x01  # 读线圈(Reading coil)
    READ_DISCRETE_INPUTS = 0x02  # 读离散量输入(Read discrete input)
    READ_HOLDING_REGISTERS = 0x03  # 读保持寄存器(Read hold register)
    READ_INPUT_REGISTER = 0x04  # 读输入寄存器(Read input register)
    WRITE_SINGLE_COIL = 0x05  # 写单个线圈(Write a single coil)
    WRITE_SINGLE_REGISTER = 0x06  # 写单个寄存器(Write a single register)
    READ_EXCEPTION_STATUS = 0x07  # 读取异常状态(Read abnormal state)
    DIAGNOSTICS = 0x08  # 诊断(diagnosis)
    GET_COM_EVENT_COUNTER = 0x0B  # 获取com事件计数器(Gets the com event counter)
    GET_COM_EVENT_LOG = 0x0C  # 获取com事件LOG(Get the com event LOG)
    WRITE_MULTIPLE_COILS = 0x0F  # 写多个线圈(Write multiple coils)
    WRITE_MULTIPLE_REGISTERS = 0x10  # 写多个寄存器(Write multiple registers)
    REPORT_SERVER_ID = 0x11  # 报告服务器ID(Report server ID)
    READ_FILE_RECORD = 0x14  # 读文件记录(Read file record)
    WRITE_FILE_RECORD = 0x15  # 写文件记录(Write file record)
    MASK_WRITE_REGISTER = 0x16  # 屏蔽写寄存器(Mask write register)
    READ_WRITE_MULTIPLE_REGISTERS = 0x17  # 读/写多个寄存器(Read/write multiple registers)
    READ_FIFO_QUEUE = 0x18  # 读取FIFO队列(Read the FIFO queue)
    READ_DEVICE_IDENTIFICATION = 0x2B  # 读设备识别码(Read the device identifier)

    # 异常码(Exception code)
    SUCCESSFUL = 0x00  # 成功(Successful)
    ILLEGAL_FUNCTION = 0x01  # 非法功能(Illegal function)
    ILLEGAL_DATA_ADDRESS = 0x02  # 非法数据地址(Illegal data address)
    ILLEGAL_DATA_VALUE = 0x03  # 非法数据值(Illegal data value)
    SERVER_DEVICE_FAILURE = 0x04  # 从站设备故障(The slave station device is faulty)
    ACKNOWLEDGE = 0x05  # 确认(verify)
    SERVER_DEVICE_BUSY = 0x06  # 从属设备忙(Slave device busy)
    MEMORY_PARITY_ERROR = 0x08  # 存储奇偶性差错(Store parity error)
    GATEWAY_PATH_UNAVAILABLE = 0x0A  # 不可用网关路径(The gateway path is unavailable)
    DEVICE_FAILED_TO_RESPOND = 0x0B  # 网关目标设备响应失败(The gateway target device fails to respond. Procedure)
    SLAVE_ADDR_ERROR = 0xFC  # 从地址错误(Slave address error)
    CRC_ERROR = 0xFD  # CRC校验错误(CRC check error)
    RECEIVE_ERROR = 0xFE  # 接收数据异常, 非ModBus标准错误(Receiving data is abnormal, non-ModBUS standard error)
    SEND_ERROR = 0xFF  # 发送数据异常, 非ModBus标准错误(Sending data is abnormal, which is not a ModBus standard error)

    CRC16_TABLE = (
        0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241, 0xC601,
        0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440, 0xCC01, 0x0CC0,
        0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40, 0x0A00, 0xCAC1, 0xCB81,
        0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841, 0xD801, 0x18C0, 0x1980, 0xD941,
        0x1B00, 0xDBC1, 0xDA81, 0x1A40, 0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01,
        0x1DC0, 0x1C80, 0xDC41, 0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0,
        0x1680, 0xD641, 0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081,
        0x1040, 0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
        0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441, 0x3C00,
        0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41, 0xFA01, 0x3AC0,
        0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840, 0x2800, 0xE8C1, 0xE981,
        0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41, 0xEE01, 0x2EC0, 0x2F80, 0xEF41,
        0x2D00, 0xEDC1, 0xEC81, 0x2C40, 0xE401, 0x24C0, 0x2580, 0xE541, 0x2700,
        0xE7C1, 0xE681, 0x2640, 0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0,
        0x2080, 0xE041, 0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281,
        0x6240, 0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
        0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41, 0xAA01,
        0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840, 0x7800, 0xB8C1,
        0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41, 0xBE01, 0x7EC0, 0x7F80,
        0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40, 0xB401, 0x74C0, 0x7580, 0xB541,
        0x7700, 0xB7C1, 0xB681, 0x7640, 0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101,
        0x71C0, 0x7080, 0xB041, 0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0,
        0x5280, 0x9241, 0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481,
        0x5440, 0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
        0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841, 0x8801,
        0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40, 0x4E00, 0x8EC1,
        0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41, 0x4400, 0x84C1, 0x8581,
        0x4540, 0x8701, 0x47C0, 0x4680, 0x8641, 0x8201, 0x42C0, 0x4380, 0x8341,
        0x4100, 0x81C1, 0x8081, 0x4040)


def Grey():
    global Grey_log
    a = 0
    while True:
        utime.sleep_ms(60000)
        a += 1
        Grey_log.debug('Grey running: {:03d} Minute'.format(a))
        if a == 60:
            _thread.delete_lock(0)
            break


def thread(func):  # 线程监控函数, 实际线程以参数传入(Thread monitoring function, the actual thread passed in as an argument)
    global Grey_log
    while True:
        try:
            func()
        except Exception as e:
            Grey_log.error("{}Because of the[{}] caught exception,restart now!!!!".format(func, e))
        finally:
            Grey_log.critical('End of the thread\r\n\r\n')
            pass  # 客户自己实现. (app to implement.)


class ModbusInit:
    def __init__(self, uartport, baudrate, databits, parity, stopbit, flowctl, rt_pin):
        self.uart = UART(uartport, baudrate, databits, parity, stopbit, flowctl)
        self.uart.control_485(rt_pin, 1)

    @staticmethod
    def divmod_low_high(addr):  # 分离高低字节(Separate high and low bytes)
        high, low = divmod(addr, 0x100)
        # Grey_log.debug("addr:0x{:04X}  high:0x{:02X}  low:0x{:02X}".format(addr, high, low))
        return high, low

    def calc_crc(self, string_byte):  # 生成CRC(Generate CRC)
        crc = 0xFFFF
        for pos in string_byte:
            crc ^= pos
            for i in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        gen_crc = hex(((crc & 0xff) << 8) + (crc >> 8))
        int_crc = int(gen_crc, 16)
        return self.divmod_low_high(int_crc)

    @staticmethod
    def split_return_bytes(ret_bytes):  # 将字符串转换二进制(Converts a string to binary)
        ret_str = binascii.hexlify(ret_bytes, ',')  # 二进制转字符串, 以','分隔.(Binary to string, separated by ','.)
        return ret_str.split(b",")  # 转换为列表, 以','分隔.(Convert to list, separated by ','.)

    def read_uart(self):  # UART接收(UART reception)
        num = self.uart.any()
        msg = self.uart.read(num)
        # Grey_log.debug('UART receive data: ')
        # for i in range(num):
        #     Grey_log.debug('0x{:02X}'.format(msg[i]))
        # ret_str = binascii.hexlify(msg, ',')  # 二进制转字符串, 以','分隔.(Binary to string, separated by ','.)
        # ret_str = self.split_return_bytes(msg)
        # Grey_log.debug('UART receive data: {}'.format(ret_str))
        return msg

    def write_uart(self, slave, const, start, *coil_qty):  # UART发送(UART Send)
        start_h, start_l = self.divmod_low_high(start)
        data = bytearray([slave, const, start_h, start_l])
        coil_qty_h = bytearray(len(coil_qty))
        coil_qty_l = bytearray(len(coil_qty))
        for i in range(len(coil_qty)):
            coil_qty_h[i], coil_qty_l[i] = self.divmod_low_high(coil_qty[i])
            data += bytearray([coil_qty_h[i], coil_qty_l[i]])
        # Grey_log.debug(data)
        crc = self.calc_crc(data)
        # Grey_log.debug("crc_high:0x{:02X}  crc_low:0x{:02X}".format(crc[0], crc[1]))
        for num in crc:
            data.append(num)
        self.uart.write(data)
        # Grey_log.debug('UART send data: ')
        # dataLen = len(data)
        # for i in range(dataLen):
        #     Grey_log.debug('0x{:02X}'.format(data[i]))
        # ret_str = self.split_return_bytes(data)
        # Grey_log.debug('')
        # Grey_log.debug('-------------------------------------------------------------------------')
        # Grey_log.debug('UART send data: {}'.format(ret_str))
        return True

    def write_single_coil(self, slave_addr, coil_address, coil_value):
        if coil_value:
            value = 0xFF00  # ON
        else:
            value = 0x0000  # OFF

        if self.write_uart(slave_addr, WRITE_SINGLE_COIL, coil_address, value):
            utime.sleep_ms(35)
            retstr = self.read_uart()
            if len(retstr) >= 8:
                retstr_temp = retstr[0:-2]
                retstr_crc = self.calc_crc(bytearray(retstr_temp))
                if (retstr_crc[0] == retstr[-2]) and (retstr_crc[1] == retstr[-1]):
                    if retstr[0] == slave_addr:
                        if retstr[1] == WRITE_SINGLE_COIL:
                            Grey_log.info(
                                "Successfully wrote coil {} at address 0x{:04X}".format("ON" if coil_value else "OFF",
                                                                                        coil_address))
                            return SUCCESSFUL
                        else:
                            Grey_log.error('Error Code: 0x{:02X} - Function mismatch'.format(ILLEGAL_FUNCTION))
                            return ILLEGAL_FUNCTION
                    else:
                        Grey_log.error('Error Code: 0x{:02X} - Slave address mismatch'.format(SLAVE_ADDR_ERROR))
                        return SLAVE_ADDR_ERROR
                else:
                    Grey_log.error('Error Code: 0x{:02X} - CRC error'.format(CRC_ERROR))
                    return CRC_ERROR
            else:
                Grey_log.error('Error Code: 0x{:02X} - Response too short'.format(RECEIVE_ERROR))
                return RECEIVE_ERROR
        else:
            Grey_log.error('Error Code: 0x{:02X} - Send failed'.format(SEND_ERROR))
            return SEND_ERROR

    def read_input_registers(self, slave_addr, starting_addr, register_qty):
        if self.write_uart(slave_addr, READ_INPUT_REGISTER, starting_addr, register_qty):
            utime.sleep_ms(200)
            retstr = modbus.read_uart()
            if len(retstr) > 4:
                retstr_temp = retstr[0:-2]
                retstr_crc = self.calc_crc(bytearray(retstr_temp))
                if (retstr_crc[0] == retstr[-2]) and (retstr_crc[1] == retstr[-1]):
                    if retstr[0] == slave_addr:
                        if retstr[1] == READ_INPUT_REGISTER:
                            if retstr[2] == (register_qty * 2):
                                ret_str = self.split_return_bytes(retstr[3:-2])
                                data1 = ret_str
                                # Grey_log.info('Read input register data: {}'.format(ret_str))
                                # Grey_log.info('--------------------------------------------------------------------------')
                                return data1
                            else:
                                Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_DATA_VALUE))
                                Grey_log.error(
                                    '-------------------------------------------------------------------------')
                                return ILLEGAL_DATA_VALUE
                        else:
                            Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_FUNCTION))
                            Grey_log.error('-------------------------------------------------------------------------')
                            return ILLEGAL_FUNCTION
                    else:
                        Grey_log.error('Error Code: 0x{:02X}'.format(SLAVE_ADDR_ERROR))
                        Grey_log.error('-------------------------------------------------------------------------')
                        return SLAVE_ADDR_ERROR
                else:
                    Grey_log.error('Error Code: 0x{:02X}'.format(CRC_ERROR))
                    Grey_log.error('-------------------------------------------------------------------------')
                    return CRC_ERROR
            else:
                Grey_log.error('Error Code: 0x{:02X}'.format(RECEIVE_ERROR))
                Grey_log.error('-------------------------------------------------------------------------')
                return RECEIVE_ERROR
        else:
            Grey_log.error('Error Code: 0x{:02X}'.format(SEND_ERROR))
            Grey_log.error('-------------------------------------------------------------------------')
            return SEND_ERROR

    def read_holding_registers(self, slave_addr, starting_addr, register_qty):
        if self.write_uart(slave_addr, READ_HOLDING_REGISTERS, starting_addr, register_qty):
            utime.sleep_ms(200)
            retstr = modbus.read_uart()
            if len(retstr) > 4:
                retstr_temp = retstr[0:-2]
                retstr_crc = self.calc_crc(bytearray(retstr_temp))
                if (retstr_crc[0] == retstr[-2]) and (retstr_crc[1] == retstr[-1]):
                    if retstr[0] == slave_addr:
                        if retstr[1] == READ_HOLDING_REGISTERS:
                            if retstr[2] == (register_qty * 2):
                                ret_str = self.split_return_bytes(retstr[3:-2])
                                data1 = ret_str
                                # Grey_log.info('Read register data: {}'.format(ret_str))
                                # Grey_log.info('--------------------------------------------------------------------------')
                                return data1
                            else:
                                Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_DATA_VALUE))
                                Grey_log.error(
                                    '-------------------------------------------------------------------------')
                                return ILLEGAL_DATA_VALUE
                        else:
                            Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_FUNCTION))
                            Grey_log.error('-------------------------------------------------------------------------')
                            return ILLEGAL_FUNCTION
                    else:
                        Grey_log.error('Error Code: 0x{:02X}'.format(SLAVE_ADDR_ERROR))
                        Grey_log.error('-------------------------------------------------------------------------')
                        return SLAVE_ADDR_ERROR
                else:
                    Grey_log.error('Error Code: 0x{:02X}'.format(CRC_ERROR))
                    Grey_log.error('-------------------------------------------------------------------------')
                    return CRC_ERROR
            else:
                Grey_log.error('Error Code: 0x{:02X}'.format(RECEIVE_ERROR))
                Grey_log.error('-------------------------------------------------------------------------')
                return RECEIVE_ERROR
        else:
            Grey_log.error('Error Code: 0x{:02X}'.format(SEND_ERROR))
            Grey_log.error('-------------------------------------------------------------------------')
            return SEND_ERROR

    def write_single_register(self, slave_addr, register_address, register_value):
        if self.write_uart(slave_addr, WRITE_SINGLE_REGISTER, register_address, register_value):
            utime.sleep_ms(100)
            retstr = modbus.read_uart()
            if len(retstr) > 4:
                retstr_temp = retstr[0:-2]
                retstr_crc = self.calc_crc(bytearray(retstr_temp))
                if (retstr_crc[0] == retstr[-2]) and (retstr_crc[1] == retstr[-1]):
                    if retstr[0] == slave_addr:
                        if retstr[1] == WRITE_SINGLE_REGISTER:
                            if (retstr[2] == (register_address >> 8)) and (retstr[3] == (register_address & 0xFF)) and (
                                    retstr[4] == (register_value >> 8)) and (retstr[5] == (register_value & 0xFF)):
                                # Grey_log.info('Writing to a single register succeeded')
                                # Grey_log.info(
                                #     '--------------------------------------------------------------------------')
                                return SUCCESSFUL
                            else:
                                Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_DATA_VALUE))
                                Grey_log.error(
                                    '-------------------------------------------------------------------------')
                                return ILLEGAL_DATA_VALUE
                        else:
                            Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_FUNCTION))
                            Grey_log.error('-------------------------------------------------------------------------')
                            return ILLEGAL_FUNCTION
                    else:
                        Grey_log.error('Error Code: 0x{:02X}'.format(SLAVE_ADDR_ERROR))
                        Grey_log.error('-------------------------------------------------------------------------')
                        return SLAVE_ADDR_ERROR
                else:
                    Grey_log.error('Error Code: 0x{:02X}'.format(CRC_ERROR))
                    Grey_log.error('-------------------------------------------------------------------------')
                    return CRC_ERROR
            else:
                Grey_log.error('Error Code: 0x{:02X}'.format(RECEIVE_ERROR))
                Grey_log.error('-------------------------------------------------------------------------')
                return RECEIVE_ERROR
        else:
            Grey_log.error('Error Code: 0x{:02X}'.format(SEND_ERROR))
            Grey_log.error('-------------------------------------------------------------------------')
            return SEND_ERROR

    def write_multiple_registers(self, slave_addr, starting_address, *register_values):
        if self.write_uart(slave_addr, WRITE_MULTIPLE_REGISTERS, starting_address, *register_values):
            utime.sleep_ms(200)
            retstr = modbus.read_uart()
            if len(retstr) > 4:
                retstr_temp = retstr[0:-2]
                retstr_crc = self.calc_crc(bytearray(retstr_temp))
                if (retstr_crc[0] == retstr[-2]) and (retstr_crc[1] == retstr[-1]):
                    if retstr[0] == slave_addr:
                        if retstr[1] == WRITE_MULTIPLE_REGISTERS:
                            register_values_len = len(register_values)
                            register_values_len_H, register_values_len_L = self.divmod_low_high(register_values_len)
                            if (retstr[2] == (starting_address >> 8)) and (retstr[3] == (starting_address & 0xFF)) and (
                                    retstr[4] == register_values_len_H) and (retstr[5] == register_values_len_L):
                                Grey_log.info('Multiple registers were written successfully')
                                Grey_log.info(
                                    '--------------------------------------------------------------------------')
                                return SUCCESSFUL
                            else:
                                Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_DATA_VALUE))
                                Grey_log.error(
                                    '-------------------------------------------------------------------------')
                                return ILLEGAL_DATA_VALUE
                        else:
                            Grey_log.error('Error Code: 0x{:02X}'.format(ILLEGAL_FUNCTION))
                            Grey_log.error('-------------------------------------------------------------------------')
                            return ILLEGAL_FUNCTION
                    else:
                        Grey_log.error('Error Code: 0x{:02X}'.format(SLAVE_ADDR_ERROR))
                        Grey_log.error('-------------------------------------------------------------------------')
                        return SLAVE_ADDR_ERROR
                else:
                    Grey_log.error('Error Code: 0x{:02X}'.format(CRC_ERROR))
                    Grey_log.error('-------------------------------------------------------------------------')
                    return CRC_ERROR
            else:
                Grey_log.error('Error Code: 0x{:02X}'.format(RECEIVE_ERROR))
                Grey_log.error('-------------------------------------------------------------------------')
                return RECEIVE_ERROR
        else:
            Grey_log.error('Error Code: 0x{:02X}'.format(SEND_ERROR))
            Grey_log.error('-------------------------------------------------------------------------')
            return SEND_ERROR



modbus = ModbusInit(_uartport, _baudrate, _databits, _parity, _stopbit, _flowctl, _control_485)


def modbus_rtu_to_decimal(data):
    if len(data) % 2 != 0:
        raise ValueError("The data length must be even.")

        # Convert byte pairs to decimal
    decimal_values = []
    for i in range(0, len(data), 2):
        # Combine two bytes into a 16-bit integer
        value = int(data[i], 16) * 256 + int(data[i + 1], 16)
        decimal_values.append(value)

    return decimal_values

def safe_read_input_registers(slave_addr, starting_addr, register_qty, sensor_name="Unknown"):
    result = modbus.read_input_registers(slave_addr, starting_addr, register_qty)
    if isinstance(result, int):  # Error code
        Grey_log.error("Device '{}' is not available. Error Code: 0x{:02X}".format(sensor_name, result))
        return None
    return result

def convert_room1_temp(room1):
    # Check if the MSB (0x8000) is set, indicating a negative number in a signed 16-bit integer
    if room1 & 0x8000:
        return room1 - 0x10000
    else:
        return room1

def calculate_press_temp(press):
    if press is None:
        temp = None
        return temp
    # Calculate evap_temp using the polynomial formula
    temp = (0.018 * (press ** 3) - 0.6912 * (press ** 2) + 10.957 * press - 29.913)
    return "{:.1f}".format(temp)

def sensor_value(value):
    if value >= 32766:
        value = None
        return value
    else:
        sensor_data = value/10
        return "{:.1f}".format(sensor_data)

def sht_value(value):
    if value <= 20 or value >= 2000:
        return None
    sensor_data = value / 10
    return "{:.2f}".format(sensor_data)

def sht_value_redu(value):
    if value <= 20 or value >= 2000:
        return None
    sensor_data1 = value/10
    sensor_data = sensor_data1-1
    return "{:.2f}".format(sensor_data)

def press_sensor_value(value):
    if value >= 3000:
        value = None
        return value
    else:
        sensor_data = value/100
        return sensor_data

def noise_value(reg):
    try:
        return reg / 10.0
    except:
        return None


# -------------------------------------------------------------------
# ENERGY METER MULTISPAN EPM 35 M1 CONFIGURATION
# -------------------------------------------------------------------

SLAVE_ID = 5                     # Change as per meter address
START_REG = 20                   # First register to read
END_REG = 92                     # Last register to read
REG_COUNT = (END_REG - START_REG) + 2   # Inclusive, float = 2 regs

EPM35_PARAM_MAP = {
    # kWh
    "kWh": 6,
    "kVArh": 10,

    # Voltages
    "v_l1_l2": 36,
    "v_l2_l3": 40,
    "v_l3_l1": 44,

    # Currents
    "i_l1": 52,
    "i_l2": 56,
    "i_l3": 60,

    # Power factor & frequency
    "pf_sys": 76,
    "kW": 92,
    "kVA": 108,
}

def decode_epm35_float(raw):
    """
    raw: list of 4 bytes coming from modbus
         Example: [b'6e', b'14', b'43', b'5c']
    """
    try:
        # Convert ASCII hex bytes → numeric bytes
        b = bytes(int(x, 16) for x in raw)
        if len(b) != 4:
            return 0.0
        # Word swap (Multispan format)
        reordered = bytes([b[2], b[3], b[0], b[1]])
        # Big-endian IEEE-754 float
        return ustruct.unpack('>f', reordered)[0]
    except Exception as e:
        log.error("Float decode error: %s", e)
        return 0.0

def get_float_from_block(block, reg_addr):
    """
    block    : full modbus response (byte list)
    reg_addr : actual modbus register address
    """
    offset = (reg_addr - START_REG) * 2
    raw_bytes = block[offset : offset + 4]
    return decode_epm35_float(raw_bytes)

def safe_round(val, decimals=2):
    if val is None:
        return 0.0
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return 0.0
        return "{:.2f}".format(val)
    return 0.0


def safe_read_epm35(slave_id, sensor_name="Energy Meter"):
    """
    Safely read Multispan EPM35 energy meter.
    If meter not available, prints error and returns None.
    """

    raw_block = modbus.read_holding_registers(slave_id, START_REG, REG_COUNT)

    # Check for communication error
    if isinstance(raw_block, int) or not raw_block:
        Grey_log.error("Device '{}' is not available.".format(sensor_name))
        return None

    # Check data length
    if len(raw_block) != REG_COUNT * 2:
        Grey_log.error("Device '{}' returned invalid data.".format(sensor_name))
        return None

    data = {}

    for name, reg in EPM35_PARAM_MAP.items():
        value = get_float_from_block(raw_block, reg)
        data[name] = safe_round(value, 2)

    return data


# -------------------------------------------------------------------
# DELTA PLC SS2 (MO-M35) BINARY ON/OFF (1/0) CONFIGURATION
# -------------------------------------------------------------------

def write_plc_output(output, data):
    # Define output coil addresses
    output_addresses = {
        0: 2048,
        1: 2049,
        2: 2050,
        3: 2051,
        4: 2052,
        5: 2053,
        6: 2054,
        7: 2055,
        8: 2056,
        9: 2057,
        10: 2058,
        11: 2059,
        12: 2568,
        13: 2569,
        35: 2088
    }

    # Check if the output is valid
    if output in output_addresses:
        address = output_addresses[output]
        modbus.write_single_coil(1, address, data)
        print("Write PLC OUTPUT -> Output: Y{} (Address: {}), Data: {}".format(output, address, data))
        return True
    else:
        print("Invalid output: {}".format(output))
        return False

# -------------------------------------------------------------------
#  EDGELOGIX SHT40 RH SENSOR & PPI CONFIGURATION
# -------------------------------------------------------------------

ENERGY_METERS = {
    "energy_meter1": 5,
    "energy_meter2": 6,
    "energy_meter3": 7
}

def modbus_sensors_data():
    data = {}  # Start with empty dictionary
    formatted = True
    # --------------- Multispan Energy Meter -----------------------

    for name, slave in ENERGY_METERS.items():
        meter = safe_read_epm35(slave, name)
        if meter:
            for key, value in meter.items():
                data["{}_{}".format(name, key)] = value

    # --- PPI Sensor 1 ---
    ppi_registers_data = safe_read_input_registers(2, 1561, 8, "PPI 1")
    if ppi_registers_data:
        reg = modbus_rtu_to_decimal(ppi_registers_data)
        data["dia_roller"] = sensor_value(reg[0])
        data["screw_conveyer_motor"] = sensor_value(reg[1])
        data["pelleting_motor"] = sensor_value(reg[2])
        data["jaw_shredder1"] = sensor_value(reg[3])
        data["jaw_shredder2"] = sensor_value(reg[4])
        data["temp1"] = sensor_value(reg[5])
        data["analog1"] = sensor_value(reg[6])
        data["analog2"] = sensor_value(reg[7])
    return data if data else {}