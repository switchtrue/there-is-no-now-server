#!/usr/bin/env bash

docker build -t gcr.io/pycon2018-213209/hello-app:v$1 .
docker push gcr.io/pycon2018-213209/hello-app:v$1
kubectl set image deployment/hello-app-1 hello-app=gcr.io/pycon2018-213209/hello-app:v$1
