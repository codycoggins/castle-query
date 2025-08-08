#!/bin/bash

docker run -d \
  --name qdrant \
  -p 6333:6333 \
  qdrant/qdrant

curl http://localhost:6333/collections

# TODO: Enable authentication for qdrant
