#!/bin/bash
PkgName='teprunner-backend'

Dockerfile='./Dockerfile'
DockerContext=../

echo "Start build image..."
docker build -f $Dockerfile -t $PkgName $DockerContext
if [ $? -eq 0 ]
then
    echo "Build docker image success"
    exit 0
else
    echo "Build docker image failed"
    exit 1
fi
