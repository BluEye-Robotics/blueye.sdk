# Controlling from the Command Line Interface

This is a super simple example showing how you make the drone move from the command line interface:

```python
import time
from blueye.sdk import Pioneer
p = Pioneer()
p.motion.surge = 1
time.sleep(1)
p.motion.surge = 0
```
