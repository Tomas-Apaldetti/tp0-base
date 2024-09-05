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

La repuesta a una peticion del cliente sera similar, con diferencia de:
- El payload de la respuesta dependera del tipo de respuesta
- En lugar de tener el campo de `clientId` tendra un codigo de respuesta `uint32 little-endian`. Este codigo de respuesta sera utilizado para indicar respuestas generales del protocolo (por ahora solamente existen `OK=200` y `ERROR=400`). Cualquier otra informacion del negocio deberia ser enviada dentro del `payload` de la respuesta.

## Ejercicio 6:
Para soportar el envio de listas de objetos, se asumio que los objetos son siempre conocidos por el receptor, y en general, que sean todos iguales. De esta manera, con simplemente indicar la cantidad de objetos en el array antes de que los datos comiencen se puede serializar. Al igual que en todo el protocolo, el tipo de dato para indicar la longitud es `uint32 little-endian` (es un poco grande en terminos practicos, pero para ilustrar el concepto, en una implementacion real probablemente sean 1 o 2 bytes)

## Ejercicio 7:
Para soportar el envio de diferentes tipos de mensajes entre el cliente y el server se agrego un `uint8` al principio del mensaje para identificar el tipo. Se asumio que los tipos de mensajes se mantendran relativamente acotados. Para facilitar el codeo, el server le responde al cliente con la cantidad de ganadores; en un escenario mas realista le responde con los DNIs de los ganadores y el cliente buscara en sus datos quienes son estos ganadores. La lista de DNIs se puede enviar utilizando el mecanismo de serializacion de listas diseñado en el ejercicio anterior o como una unica string que use separadores, etc. Como en este caso solo nos interesa la cantidad, se ahorro ese trabajo. 

### Codigo de tipos de mensajes:
- `LOAD_BETS = 1` : Mandado por el cliente para cargar apuestas. Se espera que lo siguiente sea una lista de apuestas
- `ASK = 2`: Mandado por el cliente para preguntar el ganador. No se espera payload

- `BETS_RECEIVED = 253`: Respuesta al cargar apuestas. No se espera payload
- `KEEP_ASKING = 255`: Respuesta a una pregunta de ganador que todavia no se puede responder. No se espera payload
- `ANSWER = 254`: Respuesta a una de ganador. El payload envia la cantidad de ganadores en un un `uint32 little-endian`

Para saber la cantidad de agencias esperadas se uso una variable de entorno o dentro del archivo de configuracion. En caso de usar el script de `generar-compose.sh` las agencias esperadas seran igual a la cantidad de clientes creados

## Ejercicio 8:
Para el soporte de multi threading se realizaron los siguientes cambios:
- Se utilizo una barrera para sincronizar cuando se pueden dar los resultados a las agencias. Antes se utilizaba un approach de callbacks manteniendo el socket abierto debido a que todo estaba viviendo en un unico thread.
- Se utilizo un Mutex (`Lock` en python) para bloquear el acceso al archivo de apuesta de manera que solo un handler de la agencia pueda manejarlo por vez. Debido a que la mayoria del trabajo es escibir en el archivo, solo un `thread` puede tener acceso a la vez.
- Se intenta unir los `threads` que estan terminados cada vez que se acepta una nueva conexion para poder limpiar la memoria del servidor a medida que llegan nuevos clientes. 
- El cliente ahora solo crea una conexion por donde se transmiten todos los mensajes que necesita; de todas maneras este enfoque es para no inundar de creaciones de threads el servidor (pues de la anterior manera se crearia un thread por mensaje mandado), el protocolo gracias al id del cliente puede retomar en caso de que el cliente se desconecte.

El protocolo de comunicacion se mantuvo igual