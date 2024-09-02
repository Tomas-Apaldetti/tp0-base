## Ejercicio 1:
Se debera correr `./generar-compose.sh <output_name> <client_amount>` y luego correr los comandos de `Makefile` correspondientes

## Ejercicio 2:
Correr comandos de `Makefile` correspondientes

## Ejercicio 3:
El script `validar-echo-server.sh` levanta un container, instala netcat y luego lo utiliza para mandar el mensaje. Asume una red `tp0_testing_net` container del server llamado `server` y que este sirviendo trafico en puerto `12345`

## Ejercicio 4:
No se modifico forma de correr el proyecto.

## Ejercicio 5:
Los valores de las apuestas que seran mandadas por el cliente se toman desde las variable de entorno.

### Protocolo de Comunicacion
Para el protocolo de comunicacion se decidio utilizar un protocolo binario donde tanto el servidor como el cliente deben de estar de acuerdo en el orden de los campos que se van a a pasar. Para la parte de networking del mensaje el cliente utilizara dos campos, en orden: 
1. `lenght`: `uint32 little-endian` numero para demarcar el tamaño del payload
2. `clientId`: `string` identificador del cliente. No se dio limite para el mismo para facilitar la implementación, pero en una implementacion mas formal deberia tenerlo

Luego de esto, sigue el payload, abstracto a los campos de la parte de networking. Para una apuesta, en orden:
1. `Nombre`: `string`
1. `Apellido`: `string`
1. `Documento`: `string`
1. `Nacimiento`: `string`
1. `Numero`: `uint32 little-endian`

Todos los campos de tipo `string` se serializan en encoding `utf-8` de la siguiente manera: `<largo><bytes>` donde `tamaño` se refiere al largo en bytes de la `string` en `utf-8` y es un `uint32 little-endian`.

De esta manera se permite que las apuestas tengan diferente longitud y soporten variacion en sus contenido. (A costa de utilizar un tamaño fijo para su longitud, que ademas limita el tamaño maximo de un campo string)

## Ejercicio 6:
Para soportar el envio de listas de objetos, se asumio que los objetos son siempre conocidos por el receptor, y en general, que sean todos iguales. De esta manera, con simplemente indicar la cantidad de objetos en el array antes de que los datos comiencen se puede serializar. Al igual que en todo el protocolo, el tipo de dato para indicar la longitud es `uint32 little-endian` (es un poco grande en terminos practicos, pero para ilustrar el concepto, en una implementacion real probablemente sean 1 o 2 bytes)
