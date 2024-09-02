NETWORK_INSPECT=$(docker network inspect tp0_testing_net)
: ${SERVER_IP:=$(echo "$NETWORK_INSPECT" | awk -F'"' '/"Name": "server"/ {getline; getline; getline; print $4}' | cut -d'/' -f1)}
: ${SERVER_PORT:=12345}

# Check if SERVER_IP is set
if [ -z "$SERVER_IP" ]; then
  echo "Error: SERVER_IP environment variable is not set."
  exit 1
fi

# Check if SERVER_PORT is set
if [ -z "$SERVER_PORT" ]; then
  echo "Error: SERVER_PORT environment variable is not set."
  exit 1
fi


TEST_MESSAGE="Probando"

RESPONSE=$(echo "Probando" | nc $SERVER_IP $SERVER_PORT)

if [ "$RESPONSE" = "$TEST_MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi