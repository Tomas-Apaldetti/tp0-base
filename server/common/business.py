from common import utils
from common import serialization
import logging

def deserialize_bet(client: str, b: bytes) -> utils.Bet:
    d = serialization.Deserializer(b)
    return utils.Bet(
        agency=client, 
        first_name=d.get_string(), 
        last_name=d.get_string(), 
        document=d.get_string(), 
        birthdate=d.get_string(), 
        number=d.get_int32()
    )

def handle_payload(client:str, payload: bytes):
    bet = deserialize_bet(client, payload)
    handle_bet(bet)
    logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')
    return 200, b'';

def handle_bet(bet: utils.Bet):
    utils.store_bets([bet])