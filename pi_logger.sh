#!/bin/bash
cpuTemp0=$(cat /sys/class/thermal/thermal_zone0/temp)
cpuTemp1=$(($cpuTemp0/1000))
cpuTemp2=$(($cpuTemp0/100))
cpuTempM=$(($cpuTemp2 % $cpuTemp1))
CPU=$cpuTemp1"."$cpuTempM
GPU=$(/opt/vc/bin/vcgencmd measure_temp | tr -cd '0-9.')

memTot=$(awk '/MemTotal/ { print $2 }' /proc/meminfo)
memFree=$(awk '/MemFree/ { print $2 }' /proc/meminfo)
memUsed=$(($memTot/1000-$memFree/1000))
 
curl -i -XPOST 'http://localhost:8086/write?db=breton' --data-binary 'pi_temps CPU='$CPU',GPU='$GPU'
memory_MB MEM='$memUsed