# Peripherals

The `Drone` class maintains a list of peripherals that are attached to the drone. These peripherals can include cameras, grippers, and other devices that can be controlled using the drone's API.

To list the peripherals that are currently attached to the drone, you can check the [`peripherals`][blueye.sdk.drone.Drone.peripherals] attribute of the `Drone` class. This attribute is a list of [`Peripheral`][blueye.sdk.guestport.Peripheral] objects.

The SDK also has an attribute for each supported kind of peripheral (`external_camera`, `external_light`, `gripper`, `laser`, `servo` and `skid_servo`) to simplify access. If the drone carries two devices of the same kind, the attribute refers to the last one discovered; the full set is always in `peripherals`.

## Discovery
Peripherals are discovered once per connection, from the first `DroneInfoTel` telemetry message in which the drone lists its guest ports and the devices on them. Until then, `peripherals` and `get_guest_ports()` return `None` and every peripheral attribute is `None`; a drone that has reported but has no guest ports gives empty lists. Devices plugged in or removed later in the session are not picked up until the next `connect()`. Disconnecting clears the lists and the attributes.

```python
if drone.laser is None:
    print("No scaling laser on this drone")
else:
    drone.laser.set_intensity(0.5)
```

Every [`Peripheral`][blueye.sdk.guestport.Peripheral] records which port it sits on, the interfaces it requires from that port, and which ports on the drone fully support it. For detachable devices, [`get_detach_status()`][blueye.sdk.guestport.Peripheral.get_detach_status] reports whether the device is currently attached.

## Guest ports
To see the state of each guest port, including ports with nothing connected or with a connector fault, use [`get_guest_ports()`][blueye.sdk.drone.Drone.get_guest_ports]. It returns one [`GuestPort`][blueye.sdk.guestport.GuestPort] per port the drone reports, or `None` if no guest port information has been received yet. A port either carries a list of devices or reports a connector error, never both; an empty port reports `GUEST_PORT_ERROR_NOT_CONNECTED`. Connector errors other than "not connected" are also logged as warnings when the ports are discovered.

```python
import blueye.protocol as bp

for port in drone.get_guest_ports():
    if port.error == bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED:
        print(f"{port.number.name}: empty")
    elif port.error is not None:
        print(f"{port.number.name}: connector error {port.error.name}")
    else:
        names = ", ".join(device.name for device in port.devices)
        print(f"{port.number.name}: {names}")
    print(f"  provides {[cap.name for cap in port.capabilities]}")
```

## External camera
If the drone has a camera attached, the `Drone` class will have an `external_camera` attribute that is a [`GuestPortCamera`][blueye.sdk.guestport.GuestPortCamera] object. This object can be used to control the camera.

```python
# Capture an image from the external camera
drone.external_camera.take_picture()

# Set bitrate for external camera to 2 Mbps
drone.external_camera.set_bitrate(2_000_000)

# Start recording video from the external camera
drone.external_camera.set_recording(True)
```

## External light
If the drone has an external light attached, the `Drone` class will have an `external_light` attribute that is a [`GuestPortLight`][blueye.sdk.guestport.GuestPortLight] object. This object can be used to control the light.

```python
# Get the current intensity of the external light
intensity: float = drone.external_light.get_intensity()

# Set the intensity of the external light to 0.5
drone.external_light.set_intensity(0.5)
```

## Scaling laser
If the drone has a scaling laser attached (the Blueye scaling laser, the Laser Tools Sea Beam or the Spot X laser scalers), the `Drone` class will have a `laser` attribute that is a [`Laser`][blueye.sdk.guestport.Laser] object. This object can be used to control the scaling laser. The dot spacing is 50 mm for the Blueye laser and 75 mm for the Sea Beam.

```python
# Get the current intensity of the scaling laser
intensity: float = drone.laser.get_intensity()

# Set the intensity of the scaling laser to 0.5
drone.laser.set_intensity(0.5)
```

## Gripper
If the drone has a gripper attached, the `Drone` class will have a `gripper` attribute that is a [`Gripper`][blueye.sdk.guestport.Gripper] object. This object can be used to control the grip and rotation of the gripper.

If the connected gripper does not support rotation, the rotation velocity will be ignored.

```python
# Open the gripper
drone.gripper.set_grip_velocity(1.0)

# Close the gripper
drone.gripper.set_grip_velocity(-1.0)

# Rotate the gripper clockwise
drone.gripper.set_rotation_velocity(1.0)

# Rotate the gripper counterclockwise
drone.gripper.set_rotation_velocity(-1.0)
```

## Servo
If the drone has a servo attached, the `Drone` class will either have a `servo` attribute that is a [`GenericServo`][blueye.sdk.guestport.GenericServo] object, or a `skid_servo` attribute that is a [`SkidServo`][blueye.sdk.guestport.SkidServo] object. These objects can be used to control the servo.

`skid_servo` covers every multibeam tilt servo: the skid-mounted servo (first and second generation), which tilts ±28 degrees, and the head-mounted servo, which tilts ±45 degrees. The allowed range of the connected servo is in `min_angle` and `max_angle`.

```python
# Set the angle
drone.skid_servo.set_angle(20.0)

# Get the current angle, and the angle the servo is moving towards
drone.skid_servo.get_angle()
drone.skid_servo.get_set_point()
```
