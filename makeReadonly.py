
# use with . filename!!!
#
#make my raspi readonly:
# siehe https://k3a.me/how-to-make-raspberrypi-truly-read-only-reliable-and-trouble-free/
#  https://kofler.info/raspbian-lite-fuer-den-read-only-betrieb/
# unionfs-
# http://raspberrypi.stackexchange.com/questions/5112/running-on-read-only-sd-card
#  http://www.dinotools.de/2014/03/28/raspi-arch-linux-read-only-root-fs/

# samba not working: see https://www.joachim-wilke.de/blog/2015/04/14/archlinuxarm-ro/


apt-get remove --purge wolfram-engine triggerhappy cron anacron logrotate dbus dphys-swapfile xserver-common lightdm fake-hwclock

insserv -r x11-common
apt-get autoremove --purge

apt-get install busybox-syslogd
dpkg --purge rsyslog

#ntpdate instead of fake-hwclock 
apt-get install ntpdate
# added it /etc/rc.local:
# change the ntp server according to your location
echo /usr/sbin/ntpdate -b cz.pool.ntp.org >> /etc/rc.local
pause
vi /etc/rc.local

#----------------------------------
#reroute some readwrite directories:
#if using dhcp:

rm -rf /var/lib/dhcp/
ln -s /tmp /var/lib/dhcp

#You can consider adding more symlinks from some /var subdirectories, especially run,spool and lock
rm -rf /var/run /var/spool /var/lock
ln -s /tmp /var/run 
ln -s /tmp /var/spool
ln -s /tmp /var/lock

#-----------------------------------
#remove other startup script

insserv -r bootlogs
#insserv -r sudo # if you plan to be root all the time
insserv -r alsa-utils # if you don't need alsa stuff (sound output)
#insserv -r console-setup
insserv -r fake-hwclock # probably already removed at this point..

#-----------------------------------
# Add ” ro” at the end of your  /boot/cmdline.txt line.
# /boot/cmdline.txt and append the following two at the end of the line:
echo fastboot noswap ro
pause
vi /boot/cmdline.txt

#mount fstab readonly

echo proc              /proc           proc    defaults     0       0
echo /dev/mmcblk0p1    /boot           vfat    defaults,ro  0       2
echo /dev/mmcblk0p2    /               ext4    defaults,ro  0       1
echo tmpfs             /tmp            tmpfs   defaults     0       0
pause
vi /etc/fstab


#-------------------------------------------
#Enjoy your reliable RPi. Good work! If you ever want to update the software, just remount the root filesystem as read-write temporarily:

mount -o remount,rw /

#You may want to stop watchdog temporarily. Now run your apt-get etc stuff, modify what you need.. then mount read-only again:

mount -o remount,ro /

