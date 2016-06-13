# Installation of the SDR libaries for the DVB-T dongle

The installation instructions presented here are copied from the GR_GSM wiki and slightly modified.
The installation was tested on Kali Linux.

## Install gnuradio

`apt-get install gnuradio gnuradio-dev`

## Install RTL_SDR

`apt-get install rtl-sdr librtlsdr-dev`

## Install GrOsmoSDR

`apt-get install osmo-sdr libosmosdr-dev`

## Install other prerequisites

```
sudo apt-get install cmake libboost-all-dev libcppunit-dev swig doxygen liblog4cpp5-dev python-scipy
```
```
sudo apt-get install libusb-1.0.0 libusb-dev
```

## Install libosmocore

```
sudo apt-get install cmake
sudo apt-get install build-essential libtool shtool autoconf automake git-core pkg-config make gcc
sudo apt-get install libpcsclite-dev libtalloc-dev
git clone git://git.osmocom.org/libosmocore.git
cd libosmocore/
autoreconf -i
./configure
make
sudo make install
sudo ldconfig -i
cd
```

## Install GR_GSM

```
git clone https://github.com/ptrkrysik/gr-gsm.git
cd gr-gsm
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```
Finally, we create the ~/.gnuradio/config.conf config file with nano ~/.gnuradio/config.conf. We add this two lines to it (in that GNU Radio can find custom blocks of gr-gsm):
```
[grc]
local_blocks_path=/usr/local/share/gnuradio/grc/blocks
```

## Set access to USB devices
Plug in the RTL-SDR device and check it's ID with `lsusb` command. You will see something like this:
```sh
Bus 001 Device 004: ID **0bda:2832** Realtek Semiconductor Corp. RTL2832U DVB-T
Bus 001 Device 003: ID 0424:ec00 Standard Microsystems Corp. SMSC9512/9514 Fast Ethernet Adapter
Bus 001 Device 002: ID 0424:9514 Standard Microsystems Corp.
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
```

In our case ID of the RTL.SDR device is **0bda:2832**. Now we open a rules file:
```sh
sudo nano /etc/udev/rules.d/20.rtlsdr.rules
```
...and add this line to it:
```sh
SUBSYSTEM=="usb", ATTRS{idVendor}=="0bda", ATTRS{idProduct}=="2832", GROUP="adm", MODE="0666", SYMLINK+="rtl_sdr"
```
If you are using several RTL-SDR devices, you can add several lines to this file.

Restart udev and remove/plugin your DVB-T dongle. 
