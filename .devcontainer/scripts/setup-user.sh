#!/bin/bash

set -eu

USERNAME=${1}
USER_UID=${2}
USER_GID=${3}

# add user and set them up with sudo
groupadd --gid $USER_GID $USERNAME
useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME
chmod 0440 /etc/sudoers.d/$USERNAME