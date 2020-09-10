# Controlling from the Command Line Interface

This is a super simple example showing how you make the drone move from the command line interface:

```python
import time
from blueye.sdk import Drone
myDrone = Drone()
myDrone.motion.surge = 0.4
time.sleep(1)
myDrone.motion.surge = 0
```
