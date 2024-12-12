#ARG ROS_DISTRO=humble
ARG ROS_DISTRO=jazzy
ARG WORKSPACE=/ros2


FROM osrf/ros:${ROS_DISTRO}-desktop as base

# Due to PEP668, we must isolate the system Python packages from pip-installed packages else we get the error: "error: externally-managed-environment"
# See 1st and 2nd answers from https://stackoverflow.com/questions/48561981/activate-python-virtualenv-in-dockerfile and this guide https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
#RUN apt-get update -y \
#	&& apt-get upgrade -y \
#	&& apt-get install -y python3-pip python3-venv \
#	&& python3 -m venv /opt/venv
##RUN apt-get install python3.12-venv
#ENV VIRTUAL_ENV=/opt/venv
#RUN python3 -m venv $VIRTUAL_ENV
#ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install ROS 2 Python dependencies in the virtual environment
#RUN pip install --upgrade pip \
#	&& pip install catkin_pkg empy setuptools \
#	&& pip install em==4.3.4

ARG WORKSPACE
WORKDIR ${WORKSPACE}
ENV ROS_DISTRO=${ROS_DISTRO}
SHELL ["/bin/bash", "-c"]

COPY requirements.txt .
RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install python3-pip -y \
	&& python3 -m pip install -r requirements.txt --break-system-packages # Due to PEP668, we either do this or we must isolate the system Python packages from pip-installed packages using virtualenv else we get the error: "error: externally-managed-environment". I couldn't get ROS2 jazzy to successfully install in the virtual env.
# && pip3 install -r requirements.txt


FROM base as overlay
ARG WORKSPACE
WORKDIR ${WORKSPACE}

COPY ./src/ ./src/
RUN source /opt/ros/${ROS_DISTRO}/setup.bash \
	&& colcon build


FROM overlay as run_time
ARG WORKSPACE
WORKDIR ${WORKSPACE}

COPY ./config/fastrtps-profile.xml ${WORKSPACE}/config/fastrtps-profile.xml
ENV FASTRTPS_DEFAULT_PROFILES_FILE=${WORKSPACE}/config/fastrtps-profile.xml

COPY ./entrypoints/entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh" ]
