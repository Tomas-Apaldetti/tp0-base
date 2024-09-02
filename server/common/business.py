from common import utils
from common import serialization
import logging

def deserialize_bet(client:str) -> utils.Bet:
    def deserialize(d: serialization.Deserializer) -> utils.Bet:
        return utils.Bet(
            agency=client, 
            first_name=d.get_string(), 
            last_name=d.get_string(), 
            document=d.get_string(), 
            birthdate=d.get_string(), 
            number=d.get_int32()
        )
    return deserialize;

def deserialize_bets(client: str, b: bytes) -> list[utils.Bet]:
    d = serialization.Deserializer(b)
    return d.get_list(deserialize_bet(client))

def handle_payload(client:str, payload: bytes):
    bets = deserialize_bets(client, payload)
    try:
        handle_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        return 200, b'';
    except Exception as e:
        logging.debug(e)
        logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
        return 500, b'';

def handle_bets(bets: list[utils.Bet]):
    utils.store_bets(bets)