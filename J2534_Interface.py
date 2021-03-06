# * 
# * Copyright (c) 2020, ecuunlock
# *
# * EMAIL = engineering@ecuunlock.com
# * WEBSITE = www.ecuunlock.com
# * PHONE = (419)-330-9774
# *
# * All rights reserved.
# * Redistribution and use in source and binary forms, with or without modification, 
# * are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this list 
# * of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this 
# * list of conditions and the following disclaimer in the documentation and/or other
# * materials provided with the distribution.
# * Neither the name of the organization nor the names of its contributors may be 
# * used to endorse or promote products derived from this software without specific 
# * prior written permission.
# * 
# * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# *

from J2534 import (
    Protocols,
    BaudRate,
    Ioctls,
    Filters,
    Voltages,
    PinNumber,
    Flags,
    ConnectFlags,
    TxFlags,
)
from J2534_lookup import DiagnosticFunctions as Diagnostic
from J2534_lookup import Information as information
from J2534 import Utils as Utility
from J2534 import PassThru
from DataBase import (
    Ecu_Origin,
    Supplier,
    PCM_Variant,
    Vehicle_Line,
    Platform,
    Body_Style,
    Country_Code,
    Skim_State,
)
from Unlock import UnlockAlgorithm
from binascii import unhexlify, hexlify

unlockCalc = UnlockAlgorithm()

class FormatData:
    def __init__(self):
        pass

    # Returns modified n...
    @staticmethod
    def modifyBit(n, p, b):
        mask = 1 << p
        return hex((n & ~mask) | ((b << p) & mask))

    # Returns hex to ascii...
    @staticmethod
    def f_0001(dataInput):

        dirty = dataInput

        clean = str(unhexlify(dirty).decode("utf-8"))

        if not j2534.output_string:

            return clean

        else:

            output = j2534.output_string + clean

            return output

    # Returns hex to ascii...
    @staticmethod
    def f_0000(dataInput):

        Supplier_Variant_PartNumber = []

        supplier = dataInput[2:4]

        variant = dataInput[4:6]

        partNumber = unhexlify(dataInput[20:52]).decode('utf-8')

        Supplier_Variant_PartNumber.append(supplier)

        Supplier_Variant_PartNumber.append(variant)

        Supplier_Variant_PartNumber.append(partNumber)

        if not j2534.output_string:

            return

        else:

            output = j2534.output_string + clean

            return output

formdata = FormatData()

# ============================================  INTERFACE TO J2534 LIBRARY  ===========================================
class J2534:
    def __init__(self):
        self.toolName = []
        self.toolPath = []
        self.toolConnect = []

        self.toolIndex = None
        self.baud_rate = None
        self.connect_flags = None
        self.rx_timeout = None
        self.tx_timeout = None
        self.tx_flag = None
        self.protocol = None

        self.tool = None
        self.isConnected = 'no'

        self.tx_id_address = []
        self.rx_id_address = []
        self.transmit_data = []
        self.edit_data_string = []

        self.positive_response = None
        self.output_string = None
        self.start_diagnostic_session = None
        self.data_index_start = None
        self.data_index_end = None
        self.security_level = None
        self.format_data = None
        self.communication_type = None
        self.debugger = None
        self.supplier = None
        self.variant = None

    # if you set a formatter in your function you need to set it up in here to format data output...
    def output_formatter(self, data_input):

        if self.format_data == "0001":
            return format_data.f_0001(data_input)

        if self.format_data == "0000":
            return format_data.f_0000(data_input)

        if self.format_data == "0003":
            return format_data.f_0003(data_input)

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # this will set a flag upon tool connection, so you will not try to open tool that is already open...
    def connect_flag(self, state):

        #  if flag state is set to 0 tool is not connected if set 1 connection has already been made...

        if state == 'no':

            self.isConnected = 'no'

            self.tool.pass_thru_close()

            return False

        elif state == 'yes':

            self.isConnected = 'yes'

            pass

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # ONLY USED INSIDE txNrx FUNCTION!!!, this opens connection and sets flow filters...
    def connect_tool_set_filters(self):

        if self.isConnected == 'no':

            if self.tool.pass_thru_connect(self.protocol, self.connect_flags, self.baud_rate) == 0:

                if self.flow_control_filter(self.tx_id_address[0], self.rx_id_address[0]):
                    self.connect_flag('yes')

                    return True

            else:

                self.connect_flag('no')

                return False

        else:

            return True

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # ONLY USED INSIDE txNrx FUNCTION!!!, this sets vars for tx, rx structure sends data and recieves data...
    def transmit_and_receive_data(self):

        transmit_payload = (self.tx_id_address[0] + self.transmit_data[0])  # tx id and data to be sent ..

        tx = self.tool.pass_thru_structure(self.protocol, 0, self.tx_flag, 0, len(transmit_payload),
                                           0, transmit_payload)

        rx = self.tool.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

        if self.start_diagnostic_session == "yes":

            if self.start_extended_diagnostic_session_1092():
                pass

        if self.tool.pass_thru_write(tx, 1, self.tx_timeout) == 0:

            while self.tool.pass_thru_read(rx, 1, self.rx_timeout) == 0:

                if rx.DataSize > 5:

                    if "7F" not in rx.dump_data() and self.positive_response in rx.dump_data():

                        line = rx.dump_data().replace(" ", "", rx.DataSize)

                        # if self.debugger == 'debug': print('[debug] Recieved data is = ' + line)
                        if self.debugger == "debug":
                            print("\n" + "[debugger]"), rx.dump(), print("")

                        try:

                            output = line[self.data_index_start: self.data_index_end]

                            if self.debugger == "debug" and self.data_index_start:

                                print("[debugger] Indexed output data is = " + output + "\n")

                            if not self.format_data:

                                return rx.dump_data()

                            else:

                                return self.output_formatter(output)  # send indexed data to formatter...

                        except IndexError:

                            return

                    else:

                        if self.debugger == "debug":
                            print("[debugger] Negative response data is = " + rx.dump_data() + "\n")

                        return

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    # this will configure all the data automatically for you from the function you pass to it...
    def function_builder(self, ecu_id, func_in):

        # clear all this shit for the next func...
        self.tx_id_address = []
        self.rx_id_address = []
        self.positive_response = None
        self.output_string = None
        self.start_diagnostic_session = None
        self.data_index_start = None
        self.data_index_end = None
        self.security_level = None
        self.format_data = None
        self.communication_type = None
        self.debugger = None
        self.supplier = None
        self.variant = None

        self.tx_id_address.append(ecu_id[0])

        self.rx_id_address.append(ecu_id[1])

        for item in func_in:

            if item.startswith("[tx]"):

                data = item.replace("[tx]-", "")

                data = [int(data[i: i + 2], 16) for i in range(0, len(data), 2)]

                self.transmit_data.insert(0, data)

            elif item.startswith("[rx]"):

                data = item.replace("[rx]-", "")

                data = [data[i: i + 2] for i in range(0, len(data), 2)]

                data = " ".join(map(str, data))

                self.positive_response = data

            elif item.startswith("[st]"):

                data = item.replace("[st]-", "")

                self.output_string = '\n' + data

            elif item.startswith("[dg]"):

                self.start_diagnostic_session = "yes"

            elif item.startswith("[ix]"):

                data = item.replace("[ix]-", "")

                data = data.replace(":", "")

                self.data_index_start = int(data[0:2])

                self.data_index_end = int(data[2:4])

            elif item.startswith("[sc]"):

                data = item.replace("[sc]-", "")

                self.security_level = data

            elif item.startswith("[fm]"):

                data = item.replace("[fm]-", "")

                self.format_data = data

            elif item.startswith("[debug]"):

                self.debugger = "debug"

            elif item.startswith("[tp]"):

                data = item.replace("[tp]-", "")

                self.communication_type = data

            elif item.startswith("[d1]"):

                data = item.replace("[d1]-", "")

                output = hexlify(data.encode("utf-8"))

                output = [output[i: i + 2].decode() for i in range(0, len(output), 2)]

                for item in output:
                    item = int(item, 16)

                    self.edit_data_string.append(item)

                data = self.transmit_data[0] + self.edit_data_string

                self.transmit_data.insert(0, data)

        for item in func_in:

            if item.startswith("[rx]"):
                data = (
                        " ".join("{:02X}".format(a) for a in self.rx_id_address[0])
                        + " "
                        + self.positive_response[0]
                )

                self.positive_response = data

        return True

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def identify_ecu(self):

        self.supplier.clear()

        self.variant.clear()

        level_to_unlock = self.security_level

        communication_protocol = self.communication_type

        if communication_protocol == "kwp":

            transmit_payload = self.tx_id_address[0] + [
                0x1A,
                0x87,
            ]  # tx id and data to be sent ..

            tx = self.tool.pass_thru_structure(
                self.protocol, 0, self.tx_flag, 0, len(transmit_payload), 0, transmit_payload
            )

            rx = self.tool.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

            if self.tool.pass_thru_write(tx, 1, self.tx_timeout) == 0:

                while self.tool.pass_thru_read(rx, 1, self.rx_timeout) == 0:

                    if rx.DataSize > 5:

                        if "7F" not in rx.dump_data():

                            if "5A 87" in rx.dump_data():

                                line = rx.dump_data().replace(" ", "", rx.DataSize)

                                output = [
                                    line[i:i + 2] for i in range(0, len(line), 2)
                                ]

                                self.supplier.insert(0, output[7])

                                self.variant.insert(0, output[8])

                                supplier = self.supplier[0]

                                variant = self.variant[0]

                                return supplier, variant

                            else:

                                return False

                else:

                    self.connect_flag('no')

                    return False

        return True

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def security_unlock_ecu(self):

        if self.identify_ecu():

            get_unlock_level = self.security_level

            get_communication_type = self.communication_type

            get_seed = None

            send_key = None

            level_to_unlock = None

            if get_communication_type == "kwp":
                if get_unlock_level == "level-1":
                    get_seed = [0x27, 0x01]
                    send_key = [0x27, 0x02]
                    level_to_unlock = 1
                if get_unlock_level == "level-3":
                    get_seed = [0x27, 0x03]
                    send_key = [0x27, 0x04]
                    level_to_unlock = 3
                if get_unlock_level == "level-5":
                    get_seed = [0x27, 0x05]
                    send_key = [0x27, 0x06]
                    level_to_unlock = 5
                if get_unlock_level == "level-7":
                    get_seed = [0x27, 0x07]
                    send_key = [0x27, 0x08]
                    level_to_unlock = 7
                if get_unlock_level == "level-9":
                    get_seed = [0x27, 0x09]
                    send_key = [0x27, 0x0A]
                    level_to_unlock = 9
                if get_unlock_level == "level-61":
                    get_seed = [0x27, 0x61]
                    get_seed = [0x27, 0x62]
                    level_to_unlock = 61

                transmit_payload = (
                        self.tx_id_address[0] + get_seed
                )  # tx id and data to be sent ..

                tx = self.tool.pass_thru_structure(
                    self.protocol, 0, self.tx_flag, 0, len(transmit_payload), 0, transmit_payload
                )

                rx = self.tool.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

                if self.tool.pass_thru_write(tx, 1, self.tx_timeout) == 0:

                    while self.tool.pass_thru_read(rx, 1, self.rx_timeout) == 0:

                        if rx.DataSize > 5:

                            if "7F" not in rx.dump_data():

                                if "00 00 00 00" not in rx.dump_data():

                                    key = unlock_algo.finder(
                                        rx.dump_data(),
                                        self.supplier[0],
                                        self.variant[0],
                                        level_to_unlock,
                                    )

                                    if key:

                                        transmit_payload = (
                                                self.tx_id_address[0] + send_key + key
                                        )

                                        tx = self.tool.pass_thru_structure(
                                            self.protocol,
                                            0,
                                            self.tx_flag,
                                            0,
                                            len(transmit_payload),
                                            0,
                                            transmit_payload,
                                        )

                                        rx = self.tool.pass_thru_structure(
                                            self.protocol, 0, 0, 0, 0, 0, []
                                        )

                                        if (
                                                self.tool.pass_thru_write(
                                                    tx, 1, self.tx_timeout
                                                )
                                                == 0
                                        ):

                                            while (
                                                    self.tool.pass_thru_read(
                                                        rx, 1, self.rx_timeout
                                                    )
                                                    == 0
                                            ):

                                                if rx.DataSize > 5:

                                                    if "7F" not in rx.dump_data():

                                                        if "67 02 34" in rx.dump_data():
                                                            return True

                                    else:

                                        return True

                            else:

                                if (
                                        len(self.start_diagnostic_session) == 0
                                ):  # if no diag session needed dump data...

                                    return rx.dump_data()

                                else:

                                    if self.start_diagnostic_session == "yes":

                                        if (
                                                self.start_extended_diagnostic_session_1092()
                                                and self.security_unlock_ecu()
                                        ):
                                            return True

        else:

            self.connect_flag('no')

            return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def flow_control_filter(self, tx, rx):

        mask = self.tool.pass_thru_structure(
            j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, [0xFF, 0xFF, 0xFF, 0xFF]
        )

        pattern = self.tool.pass_thru_structure(
            j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, rx
        )

        flow_control = self.tool.pass_thru_structure(
            j2534.protocol, 0, j2534.tx_flag, 0, 4, 0, tx
        )

        err, msg_id = self.tool.pass_thru_start_msg_filter(
            Filters.FLOW_CONTROL_FILTER, mask, pattern, flow_control
        )

        if err == 0:

            return True

        else:

            return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def select_tool_load_library(self, data):

        if len(data) != 7:
            return False

        self.toolIndex = data[0]

        self.protocol = data[1]

        self.tx_flag = data[2]

        self.rx_timeout = data[3]

        self.tx_timeout = data[4]

        self.connect_flags = data[5]

        self.baud_rate = data[6]

        self.tool = PassThru(device_index=self.toolIndex)

        if self.tool.pass_thru_open() == 0:  # open device

            firmware_version, dll_version, api_version = self.tool.pass_thru_version()

            firmware_version = firmware_version.decode("utf-8")

            return firmware_version

        else:

            self.connect_flag('no')

            return False

    # DO NOT CALL THIS IT IS AN INTERNAL FUNCTION YOU DO NOT NEED TO TOUCH IT!!!...
    def start_extended_diagnostic_session_1092(self):

        transmit_payload = self.tx_id_address[0] + [0x10, 0x92]  # tx id and data to be sent ..

        transmit_payload_length = len(transmit_payload)  # length of tx id and data...

        tx = self.tool.pass_thru_structure(
            self.protocol, 0, self.tx_flag, 0, transmit_payload_length, 0, transmit_payload
        )

        rx = self.tool.pass_thru_structure(self.protocol, 0, 0, 0, 0, 0, [])

        if self.connect_tool_set_filters():

            if self.tool.pass_thru_write(tx, 1, self.tx_timeout) == 0:

                while self.tool.pass_thru_read(rx, 1, self.rx_timeout) == 0:

                    if rx.DataSize > 5:

                        if "7F" not in rx.dump_data():

                            if "50 92" in rx.dump_data():
                                return True

        else:

            self.connect_flag('no')

            return False

    # this will list all the j2534 tools that are installed on your computer...
    def list_available_tools(self):

        count = 0

        try:

            for item in PassThru().DeviceList:
                self.toolName.append(item[0])

                self.toolPath.append(item[1])

                count += 1

            return [self.toolName, self.toolPath]

        except IndexError:

            return

    # this is the main function you pass your function list to then it does the rest...
    def transmit_and_receive(self, ecu_id, data_input):

        if self.function_builder(ecu_id, data_input) and self.connect_tool_set_filters():

            if not self.security_level:

                return self.transmit_and_receive_data()

            else:

                if self.security_unlock_ecu():

                    return self.transmit_and_receive_data()

                else:

                    return False

    @staticmethod
    def connect_29bit_can(j2534_tool_index):
        open_j2534_tool = j2534.select_tool_load_library(
            [
                j2534_tool_index,
                Protocols.ISO15765,
                TxFlags.ISO15765_CAN_ID_29,
                250,
                250,
                ConnectFlags.CAN_29BIT_ID,
                BaudRate.CAN_500000,
            ]
        )
        return open_j2534_tool

    @staticmethod
    def connect_11bit_can(j2534_tool_index):
        open_j2534_tool = j2534.select_tool_load_library(
            [
                j2534_tool_index,
                Protocols.ISO15765,
                TxFlags.ISO15765_FRAME_PAD,
                250,
                250,
                ConnectFlags.NONE,
                BaudRate.CAN_500000,
            ]
        )
        return open_j2534_tool


j2534 = J2534()
# =======================================================  END  =======================================================


# ================================================= SET TOOL CONNECTION ===============================================
class Connection:
    def __init__(self):
        pass

    def Can(self, tool):
        openTool = j2534.open([tool,
                    Protocols.ISO15765,
                    TxFlags.ISO15765_FRAME_PAD,
                    250,
                    250,
                    ConnectFlags.NONE,
                    BaudRate.CAN_500000
                    ])
        return openTool

    def extCan(self, tool):
        openTool = j2534.open([tool,
                    Protocols.ISO15765,
                    TxFlags.ISO15765_CAN_ID_29,
                    250,
                    250,
                    ConnectFlags.CAN_29BIT_ID,
                    BaudRate.CAN_500000
                    ])
        return openTool

connect = Connection()
# =======================================================  END  =======================================================


# ====================================  SET TX & RX ID'S FOR ALL MODULES BEING USED   =================================
class ModuleTxRxId:
    def __init__(self):
        return

    ecu = [
        [0x00, 0x00, 0x07, 0xE0],  # hex format tx data
        [0x00, 0x00, 0x07, 0xE8],  # hex format rx data
    ]

    ecu2 = [
        [0x18, 0xDA, 0x10, 0xF1],  # hex format tx data
        [0x18, 0xDA, 0xF1, 0x10],  # hex format rx data
    ]

    tipm = [
        [0x00, 0x00, 0x06, 0x20],  # hex format tx data
        [0x00, 0x00, 0x05, 0x04],  # hex format rx data
    ]

module = ModuleTxRxId()
# =======================================================  END  =======================================================


# ======================================  LIST TOOLS INSTALLED ON THIS COMPUTER  ======================================
# this for loop will list one tool per line uncomment which one you want to use...
for tool in j2534.tools()[0]: print(tool)  #  this will print tool name
# for tool in j2534.tools()[1]: print(tool)  # this will print tool dll path

# this way will print a list containing all the tools installed
# print(j2534.tools()[0])  #  this will print tool name
# print(j2534.tools()[1])  #  this will print tool dll path
# =======================================================  END  =======================================================


# ===========================================  OPEN TOOL AND SET PARAMETERS  ==========================================
# by using print(connect.extCan(1)) it will print tool name, firmware, serial number...
# example 'connect.extCan(1)'  the 1 that is passed is the tools index you want to use...
# REMEMBER INDEX STARTS AT 0 NOT 1 ONE uncomment which one you want to use...
# print(connect.extCan(1))

# use this without print if you want to open without printing all tools info...
# example connect.extCan(1)
connect.extCan(1)
# connect.Can(1)
# =======================================================  END  =======================================================


udsVinCurrent = [
            '[tx]-22f190',
            '[rx]-62F190',
            '[st]-[i] Current Vin Number ',
            '[dg]-yes',
            '[ix]-14:48',
            '[fm]-0001',
            '[tp]-uds'
        ]
udsVinOriginal = [
            '[tx]-22f1A0',
            '[rx]-62F1A0',
            '[st]-[i] Original Vin Number ',
            '[dg]-yes',
            '[ix]-14:48',
            '[sc]-level-1',
            '[fm]-0001',
            '[tp]-uds'
        ]
udsReset = [
            '[tx]-1101',
            '[rx]-5101',
            '[dg]-yes',

]


SupplierVariant = [
    '[tx]-1A87',
    '[rx]-5A87',
    '[ix]-12:52',
    '[fm]-0000',
    '[tp]-kwp',
    '[debug]'
        ]
VinCurrent = [
    '[tx]-1A90',
    '[rx]-5A90',
    '[st]-[i] Current Vin Number ',
    '[ix]-12:46',
    '[fm]-0001',
    '[tp]-kwp',
    '[debug]'
        ]
VinOriginal = [
    '[tx]-1A88',
    '[rx]-5A88',
    '[st]-[i] Original Vin Number ',
    '[ix]-12:46',
    '[fm]-0001',
    '[tp]-kwp'
        ]
PartNumber = [
    '[tx]-1A87',
    '[rx]-5A87',
    '[st]-[i] Part Number ',
    '[ix]-32:52',
    '[fm]-0001',
    '[tp]-kwp'
        ]

Reset = [
    '[tx]-1101',
    '[rx]-5192',
    '[dg]-yes',
    '[tp]-kwp'
]
EditVinOriginal = [
    '[tx]-3B90',
    '[rx]-7B90',
    '[tp]-kwp',
    '[dg]-yes',
    '[d1]-1C4PJLCB8EW313490'
        ]


if __name__ == '__main__':
    
    print(j2534.txNrx(module.ecu2, VinCurrent))  # LOOK LOOK(-)(-) 'j2534.txNrx(module.ecu2, VinCurrent)' INSIDE FUNCTION PARAMETERS
                                                 # THE 'module.ecu2' IS SETTING THE EXTENDED CAN 29BIT IDENTIFIERS FOR ECU. IF YOU WANT
                                                 # TO SET 11BIT ECU IDENTIFIERS JUST CALL 'module.ecu'. SETUP YOUR OTHER ECU ADDRESSES
                                                 # UNDER 'class ModuleTxRxId:' TO SETUP FOR OTHER MODULES YOU PLAN ON TALKING TO...
                                                 # TO PRINT THE OUTPUT '[i] Current Vin Number 1C4PJLCB8EW313490' TO THE TERMINAL
                                                 # DONT FORGET TO CALL THE FUNCTION INSIDE THE Print('function here') FUNCTION!!!!...

    # THIS FUNCTION ABOVE RETURNS = '[i] Original Vin Number 1C4PJLCB8EW313490'



    # print(j2534.txNrx(module.ecu2, ['[tx]-1A87'])) # CALLING FUNCTION LIKE THIS IS THE EASIEST AND FASTEST WAY TO GET DATA OUT TO
                                                     # AND BACK TO YOU. SO JUST SET YOUR PARAMS 'module.ecu2, ['[tx]-1A87']' AND WRAP
                                                     # IT WITH PRINT AND IT WILL RETURN THE RAW DATA RECIEVED THAT EASY!!!!...
        
 

