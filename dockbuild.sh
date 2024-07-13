#!/usr/bin/env bash
dock_name=lailainux/pyclientdev22x
if [[ $1 == "save" ]]; then
  tarname=$(basename $dock_name)
  docker save $dock_name > "$tarname.tar"
  exit
fi
if [[ $1 == "load" ]]; then
  tarname=$(basename $dock_name)
  docker load < "$tarname.tar"
  exit
fi
if [[ $1 == "push" ]]; then
  docker push $dock_name
  exit
fi
if [[ $1 == "create" ]]; then
  sudo docker build -t $dock_name .
  exit
fi
uid=$(id -u)
gid=$(id -g)
home=$(pwd)/home
if [[ ! -d "$home" ]]; then
  mkdir -p $home
fi
# docker run  \
docker run --user "$uid:$gid" \
  -v /home/z/dev:/home/ubuntu/dev \
  -v $home:/home/ubuntu \
  --workdir "$(realpath ..)" -it $dock_name
