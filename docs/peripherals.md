# Peripherals

The `Drone` class maintains a list of peripherals that are attached to the drone. These peripherals can include cameras, grippers, and other devices that can be controlled using the drone's API.

To list the peripherals that are currently attached to the drone, you can check the [`peripherals`][blueye.sdk.drone.Drone.peripherals] attribute of the `Drone` class. This attribute is a list of [`Peripheral`][blueye.sdk.guestport.Peripheral] objects.

The SDK will also create attributes for supported peripherals to simplify access.

## External camera
If the drone has a camera attached, the `Drone` class will have an `external_camera` attribute that is a [`GuestPortCamera`][blueye.sdk.guestport.GuestPortCamera] object. This object can be used to control the camera.

```python
# Capture an image from the external camera
drone.external_camera.take_picture()

# Set bitrate for external camera to 2 Mbps
drone.external_camera.bitrate = 2_000_000

# Start recording video from the external camera
drone.external_camera.is_recording = True
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
If the drone has a scaling laser attached, the `Drone` class will have a `laser` attribute that is a [`Laser`][blueye.sdk.guestport.Laser] object. This object can be used to control the scaling laser.

```python
# Get the current intensity of the scaling laser
intensity: float = drone.laser.get_intensity()

# Set the intensity of the scaling laser to 0.5
drone.laser.set_intensity(0.5)
```

## Gripper
If the drone has a gripper attached, the `Drone` class will have a `gripper` attribute that is a [`Gripper`][blueye.sdk.guestport.Gripper] object. This object can be used to control the grip and rotation of the gripper.

If the connected gripper does not support rotation, the `rotation_velocity` property will be ignored.

```python
# Open the gripper
drone.gripper.grip_velocity = 1.0

# Close the gripper
drone.gripper.grip_velocity = -1.0

# Rotate the gripper clockwise
drone.gripper.rotation_velocity = 1.0

# Rotate the gripper counterclockwise
drone.gripper.rotation_velocity = -1.0
```
