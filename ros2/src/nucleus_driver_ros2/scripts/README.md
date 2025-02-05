# Scripts

## example.py

Example script demonstrating how to start and subscribe to topics on the DVL.
It can be ran in a separate instance within the container as following:
```
python3 src/nucleus_driver_ros2/scripts/example.py -s /dev/ttyUSB0
```

## run_and_bag.py

Starts, subscribes and bags all topics on the DVL.

First, start the usual container after the DVL has been connected (you may have to change port permissions, e.g. `chmod 666 /dev/ttyUSB<port>`. This will automatically start the nucleus_node:
```
docker run --name=Nucleus-Node -it --rm --device=/dev/ttyUSB2:/dev/ttyUSB2  -v ~/nucleus_driver/ros2/src:/ros2/src -v ~/nucleus_driver_bags:/data nucleus_driver_ros2_jazzy bash -c "ros2 run nucleus_driver_ros2 nucleus_node"
```

Start another instance:
```
docker exec -it Nucleus-Node /bin/bash
```

Within this instance do:
```
python3 src/nucleus_driver_ros2/scripts/run_and_bag.py -s /dev/ttyUSB0
```
It will save the bag to `/data/`.


## offline_repose_calculator.py

Subscribes to AHRS and Water Track topics.

First, start the usual container, but omit the device mapping:

```
ros2 run --name=Nucleus-Node -it --rm -v ~/nucleus_driver/ros2/src:/ros2/src -v ~/nucleus_driver_data:/data nucleus_driver_ros2_jazzy bash
```

Within this container do:
```
ros2 bag play /data/bag
```

Start another instance:
```
docker exec -it Nucleus-Node /bin/bash
```

Within this instance do:
```
python3 src/nucleus_driver_ros2/scripts/offline_repose_calculator.py --output-file /data/file.csv
```

When `CTRL-C` is used to stop the script, it will finish recording topics and proceed to find closest in-time pairs of AHRS and Water Track packets and then write those to a csv file of the provided name.
