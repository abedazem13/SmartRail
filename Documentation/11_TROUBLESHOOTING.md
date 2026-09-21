# 11 — Troubleshooting

## Noisy readings

**Symptom:** the `noise` column is above ~150 mV, or `dist` jumps by more than a few cm on a still object.

| Likely cause (in order) | Diagnostic | Fix |
|---|---|---|
| No / badly placed 10 µF capacitor | Inspect | Fit it across VIN/GND right next to the sensor, correct polarity |
| Loose connection (thin sensor wires) | Press on wires, watch for synchronized jumps | Reseat, shorten wires |
| Breadboard rails not powered | Multimeter between rails | Jumper VIN → + rail, GND → − rail |
| Sunlight / other IR source | Close blinds, compare | Document as an environmental limitation |
| Second sensor aimed at the same area | Cover one sensor | Separate or angle them apart |
| Mounting too far (noise in cm grows with distance) | Check baseline | Move the sensor closer, keep baseline ≤ ~65 cm |

**Workaround without a capacitor:** the ~40 cm empty/occupied gap is much larger than typical noise, so detection still works. Powering the sensor from a separate power bank with a **common GND** also reduces supply interaction.

## Reading goes UP when an object is very close

Expected. Below ~8 cm the sensor curve reverses. Mount the sensor so nothing can get closer than ~15 cm.

## State flickers between EMPTY and OCCUPIED

The gap between the two states is too small for the margins. Record baseline and occupied distance, set `MARGIN_ENTER_CM` to about half the gap, keep `MARGIN_EXIT_CM` lower. If needed, remount the sensor to increase the gap.

## Board not detected / no COM port

1. Try another USB cable — many are charge-only.
2. Device Manager should show "Silicon Labs CP210x USB to UART Bridge (COMx)". If not, install the CP210x VCP driver from Silicon Labs.
3. Linux: add your user to the `dialout` group.

## Upload fails with "Failed to connect"

CP2102 boards normally enter download mode automatically. If not: hold **BOOT**, start the upload, release when "Connecting…" appears.

## Serial monitor shows garbage

Set the monitor to 115200 baud.

## Compile warning about `ADC_11db`

Harmless. The firmware selects `ADC_ATTEN_DB_12` automatically on core 3.x.

## Analog reads fail once WiFi is added

The pin is on ADC2. Use GPIO32–39 only.
