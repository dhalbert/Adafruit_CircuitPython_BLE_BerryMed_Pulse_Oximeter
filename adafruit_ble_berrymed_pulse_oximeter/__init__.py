# The MIT License (MIT)
#
# Copyright (c) 2020 Dan Halbert for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_ble_berrymed_pulse_oximeter`
================================================================================

BLE Support for Berrymed Pulse Oximeters


* Author(s): Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* BM1000C, made by Shanghai Berry Electronic Tech Co.,Ltd

  Protocol defined here: https://github.com/zh2x/BCI_Protocol
  Thanks as well to:
      https://github.com/ehborisov/BerryMed-Pulse-Oximeter-tool
      https://github.com/ScheindorfHyenetics/berrymedBluetoothOxymeter

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

# imports

from collections import namedtuple
import struct

from .adafruit_ble_transparent_uart import TransparentUARTService

__version__ = "0.0.0-auto.0"
__repo__ = (
    "https://github.com/adafruit/Adafruit_CircuitPython_BLE_BerryMed_Pulse_Oximeter.git"
)


PulseOximeterValues = namedtuple(
    "PulseOximeterValues", ("valid", "spo2", "pulse_rate", "pleth", "finger_present"),
)
"""Namedtuple for measurement values.

.. py:attribute:: PulseOximeterValues.valid

        ``True` if sensor readings are not valid right now

.. py:attribute:: PulseOximeterValues.finger_present

        ``True`` if finger present.

.. py:attribute:: PulseOximeterValues.spo2

        SpO2 value (int): 0-100%: blood oxygen saturation level.

.. py:attribute:: PulseOximeterValues.pulse_rate

        Pulse rate, in beats per minute (int).

.. py:attribute:: PulseOximeterValues.pleth

        Plethysmograph value, 0-100 (int).

For example::

    bpm = svc.values.pulse_rate
"""


class BerryMedPulseOximeterService(TransparentUARTService):
    """Service for reading from a BerryMed BM1000C or BM100E Pulse oximeter."""

    @property
    def values(self):
        """All the pulse oximeter values, returned as a PulseOximeterValues
        namedtuple.

        Return ``None`` if no data available.
        """
        first_byte = self.read(1)
        # Wait for a byte with the high bit set, which indicates the beginning
        # a data packet.
        if not first_byte:
            return None
        header = first_byte[0]
        if header & 0x80 == 0:
            # Not synchronized.
            return None

        data = self.read(4)
        if not data or len(data) != 4:
            return None

        # Ignoring these values, which aren't that interesting.
        #
        # pulse_beep = bool(header & 0x40)
        # probe_unplugged = bool(header & 0x20)
        #
        # Bar graph height: not sure what this is measuring
        # bar_graph = data[1] & 0x0F
        #
        # This is the device sensor signal, not the BLE signal.
        # has_sensor_signal = bool(header & 0x010)
        # sensor_signal_strength = header & 0x0F
        #
        # Acquiring pulse value
        # pulse_search = bool(data[1] & 0x20)

        # Plethysmograph value, 0-100.
        pleth = data[0]

        # Finger detected
        finger_present = not bool(data[1] & 0x10)

        # Pulse rate: 255 if invalid.
        # The high bit of the pulse rate is sent in a different byte.
        pulse_rate = data[2] | (data[1] & 0x40) << 1

        # SpO2: 0-100, or 127 if invalid
        spo2 = data[3]

        valid = spo2 != 127

        return PulseOximeterValues(
            valid=valid,
            finger_present=finger_present,
            spo2=spo2,
            pulse_rate=pulse_rate,
            pleth=pleth,
        )
