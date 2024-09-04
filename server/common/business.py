from common import utils
from common import serialization
from common import server_constants
from typing import Callable, Union
import logging

LOAD_BETS = 1
ASK = 2

BETS_RECEIVED = 253
KEEP_ASKING = 255
ANSWER = 254

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

def deserialize_bets(client: str, d: serialization.Deserializer) -> list[utils.Bet]:
    return d.get_list(deserialize_bet(client))

def handle_load_bets(client: str, d: serialization.Deserializer):
    bets = deserialize_bets(client, d)
    try:
        handle_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        return server_constants.ResponseCodes.OK, serialization.Serializer().push_uint8(BETS_RECEIVED).to_bytes();
    except Exception as e:
        logging.debug(e)
        logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
        return server_constants.ResponseCodes.ERROR, serialization.Serializer().push_str("There was an error saving the bets").to_bytes();

def handle_winner_ask_factory(client:str) -> Callable[[], tuple[int, bytes]]:
    def handle_winner_ask():
        bets = utils.load_bets()
        winners_for_agency = [bet for bet in bets if utils.has_won(bet) and bet.agency == int(client)]
        return (
            server_constants.ResponseCodes.OK, 
            serialization.Serializer().push_uint8(ANSWER).push_uint32(len(winners_for_agency)).to_bytes()
        )
    return handle_winner_ask


def handle_payload(client:str, payload: bytes) -> Union[tuple[int, bytes], Callable[[], tuple[int, bytes]]]:
    d = serialization.Deserializer(payload)
    t = d.get_uint8()
    if t == LOAD_BETS:
        return handle_load_bets(client, d)
    if t == ASK:
        return handle_winner_ask_factory(client)
    return server_constants.ResponseCodes.ERROR, serialization.Serializer().push_str("Unknown action code")

def handle_bets(bets: list[utils.Bet]):
    utils.store_bets(bets)