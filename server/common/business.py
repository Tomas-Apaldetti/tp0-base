from common import utils
from common import serialization
from common import server_constants
from typing import Callable, Union
from threading import Barrier
import logging

LOAD_BETS = 1
ASK = 2

BETS_RECEIVED = 253
KEEP_ASKING = 255
ANSWER = 254

class AgencyClient:

    def __init__(self, client_id: str, lottery_time: Barrier, safe_storage: utils.SafeBetStorage):
        self.agency_id: str = client_id
        self.lottery_time: Barrier = lottery_time
        self.storage = safe_storage

    def handle_payload(self, payload: bytes) -> tuple[int, bytes]:
        d = serialization.Deserializer(payload)
        t = d.get_uint8()
        if t == LOAD_BETS:
            return self.handle_load_bets(d)
        if t == ASK:
            self.lottery_time.wait()
            return self.handle_winner_ask()
        return server_constants.ResponseCodes.ERROR, serialization.Serializer().push_str("Unknown action code")
    
    def handle_winner_ask(self):
        bets = self.storage.load_bets()
        winners_for_agency = [bet for bet in bets if utils.has_won(bet) and bet.agency == int(self.agency_id)]
        return (
            server_constants.ResponseCodes.OK, 
            serialization.Serializer().push_uint8(ANSWER).push_uint32(len(winners_for_agency)).to_bytes()
        )

    def handle_load_bets(self, d: serialization.Deserializer):
        bets = self.deserialize_bets(d)
        try:
            self.storage.store_bets(bets)
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
            return server_constants.ResponseCodes.OK, serialization.Serializer().push_uint8(BETS_RECEIVED).to_bytes();
        except Exception as e:
            logging.debug(e)
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: {len(bets)}')
            return server_constants.ResponseCodes.ERROR, serialization.Serializer().push_str("There was an error saving the bets").to_bytes();

    def deserialize_bet(self, d: serialization.Deserializer) -> utils.Bet:
        return utils.Bet(
            agency=self.agency_id, 
            first_name=d.get_string(), 
            last_name=d.get_string(), 
            document=d.get_string(), 
            birthdate=d.get_string(), 
            number=d.get_int32()
        )

    def deserialize_bets(self, d: serialization.Deserializer) -> list[utils.Bet]:
        return d.get_list(self.deserialize_bet)
class ClientFactory:

    def __init__(self, expected_agencies, shared_storage):
        self.lottery_time = Barrier(expected_agencies)
        self.shared_storage = shared_storage
        self.agencies = {}

    def handler_for(self, client_id) -> Callable[[bytes],tuple[int, bytes]]:
        a = self.get_or_create(client_id)
        return a.handle_payload

    def get_or_create(self, client_id:str) -> AgencyClient:
        a = self.agencies.get(client_id)
        if not a:
            self.agencies[client_id] = AgencyClient(client_id, self.lottery_time, self.shared_storage)
            return self.agencies[client_id]
        return a