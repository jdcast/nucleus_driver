ARG ROS_DISTRO=jazzy
ARG WORKSPACE=/ros2

FROM osrf/ros:${ROS_DISTRO}-desktop as base

ARG WORKSPACE
WORKDIR ${WORKSPACE}
ENV ROS_DISTRO=${ROS_DISTRO}
SHELL ["/bin/bash", "-c"]

COPY requirements.txt .
RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install python3-pip -y \
	&& python3 -m pip install -r requirements.txt --break-system-packages # Due to PEP668, we either do this or we must isolate the system Python packages from pip-installed packages using virtualenv else we get the error: "error: externally-managed-environment". I couldn't get ROS2 jazzy to successfully install in the virtual env.

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
