# Plotting
This example shows how one can pull a log file from the drone and use
[pandas](https://pandas.pydata.org/) and [matplotlib](https://matplotlib.org/) to plot
it.

We'll start by downloading a log file from the drone

```python
from blueye.sdk import Pioneer

p = Pioneer()

p.logs[0].download(outputName="log0.csv")
```

We can now read the csv-file into a pandas object for easy manipulation

```python
import pandas

divelog = pandas.read_csv("log0.csv")
```

and then we'll convert the unix timestamp in `rt_clock` into a more readable format:

```python
divelog["rt_clock"] = pandas.to_datetime(divelog["rt_clock"], unit="s")
```

Next we will plot depth vs time with matplotlib:


```python
import matplotlib.pyplot as plt

# Instantiate our figure and axes to plot on
figure, axes = plt.subplots()

x = divelog["rt_clock"]
y = divelog["depth"] / 1000  # Dividing by 1000 to get depth in meters

# Plot the depth values against time
axes.plot(x, y, label="depth")

# Set title, labels, and legend
plt.title("Depth chart")
plt.xlabel("Time")
plt.ylabel("Depth [m]")
plt.legend()

# Save the figure
figure.savefig("depth_plot.svg")
```

This should yield us a plot that looks something like this:
![plot](../../media/depth_plot.svg)

See the [matplotlib documentation](https://matplotlib.org/contents.html) for more ways
to plot your data.
