TEST_MESSAGE="Probando"

RESPONSE=$(docker run --rm --name test --network tp0_testing_net alpine:latest sh -c 'apk add --no-cache netcat-openbsd > /dev/null && echo "Probando" | nc -w 1 server 12345')
if [ "$RESPONSE" = "$TEST_MESSAGE" ]; then
    echo "action: test_echo_server | result: success"
else
    echo "action: test_echo_server | result: fail"
fi