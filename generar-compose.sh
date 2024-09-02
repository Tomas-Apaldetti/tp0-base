#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <output_file> <number_of_clients>"
    exit 1
fi

# Read the parameters
NUM_CLIENTS=$2
OUTPUT_FILE=$1


# Start building the Docker Compose content
cat <<EOF > "$OUTPUT_FILE"
version: '3.8'
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
EOF

# Add the client services
for i in $(seq 1 $NUM_CLIENTS); do
    cat <<EOF >> "$OUTPUT_FILE"
  client$i:
    container_name: client$i
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID=$i
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
EOF
done

# Add the networks section
cat <<EOF >> "$OUTPUT_FILE"
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOF

echo "Docker Compose file written to $OUTPUT_FILE"