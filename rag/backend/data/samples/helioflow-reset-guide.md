# How to reset a HelioFlow 3 irrigation controller

The HelioFlow 3 is a six-zone garden irrigation controller. A reset clears skipped watering days and frozen rain-sensor state. It does not erase Wi-Fi credentials unless you hold the dial on Factory.

## Soft reset (keeps programs)

1. Turn the dial to OFF.
2. Press and hold the rain-sensor bypass button for five seconds until the display blinks `rst`.
3. Release, then turn the dial to AUTO. Zone LEDs should scan left to right once.

Use a soft reset after a power flicker or when zone 4 stays stuck on.

## Program reset (clears schedules, keeps Wi-Fi)

1. Turn the dial to SET CLOCK.
2. Press the minus and plus buttons together for eight seconds.
3. When `P-CLR` appears, press ENTER. Default watering is 6:00 AM for 10 minutes on zones 1–3, odd calendar days.

## Factory reset

Only use factory reset if the unit will not join a new network. Turn the dial to OFF, then press ENTER + bypass for twelve seconds until `FACT` appears. After reboot, SSID `HelioFlow-setup` is broadcast for ten minutes.

## Rain sensor

If the controller skips watering after dry weather, the sensor may be latched. Disconnect the sensor wires on terminals RS and C, wait thirty seconds, reconnect, then run a soft reset. The sensor must read open-circuit when dry.

## Manual zone test

Turn the dial to MANUAL, pick a zone with plus/minus, press ENTER. A test run lasts two minutes. Stop early by turning the dial to OFF. Do not test when a freeze advisory is below 2°C; valves can crack.
