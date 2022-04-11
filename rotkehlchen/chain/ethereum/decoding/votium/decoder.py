from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from rotkehlchen.accounting.structures import (
    HistoryBaseEntry,
    HistoryEventSubType,
    HistoryEventType,
    get_tx_event_type_identifier,
)
from rotkehlchen.chain.ethereum.decoding.interfaces import DecoderInterface
from rotkehlchen.chain.ethereum.decoding.structures import ActionItem, TxEventSettings
from rotkehlchen.chain.ethereum.structures import EthereumTxReceiptLog
from rotkehlchen.chain.ethereum.types import string_to_ethereum_address
from rotkehlchen.chain.ethereum.utils import asset_normalized_value, ethaddress_to_asset
from rotkehlchen.types import ChecksumEthAddress, EthereumTransaction
from rotkehlchen.utils.misc import hex_or_bytes_to_address, hex_or_bytes_to_int

if TYPE_CHECKING:
    from rotkehlchen.accounting.pot import AccountingPot

VOTIUM_CLAIM = b'Gf\x92\x1f\\Ydm"\xd7\xd2f\xa2\x91d\xc8\xe9b6\x84\xd8\xdf\xdb\xd91s\x1d\xfd\xca\x02R8'  # noqa: E501
VOTIUM_CONTRACT = string_to_ethereum_address('0x378Ba9B73309bE80BF4C2c027aAD799766a7ED5A')

CPT_VOTIUM = 'votium'


class VotiumDecoder(DecoderInterface):  # lgtm[py/missing-call-to-init]

    def _decode_claim(  # pylint: disable=no-self-use
        self,
        tx_log: EthereumTxReceiptLog,
        transaction: EthereumTransaction,  # pylint: disable=unused-argument
        decoded_events: List[HistoryBaseEntry],
        all_logs: List[EthereumTxReceiptLog],  # pylint: disable=unused-argument
        action_items: Optional[List[ActionItem]],  # pylint: disable=unused-argument
    ) -> Tuple[Optional[HistoryBaseEntry], Optional[ActionItem]]:
        if tx_log.topics[0] != VOTIUM_CLAIM:
            return None, None

        claimed_token_address = hex_or_bytes_to_address(tx_log.topics[1])
        claimed_token = ethaddress_to_asset(claimed_token_address)
        if claimed_token is None:
            return None, None

        receiver = hex_or_bytes_to_address(tx_log.topics[2])
        claimed_amount_raw = hex_or_bytes_to_int(tx_log.data[32:64])
        amount = asset_normalized_value(amount=claimed_amount_raw, asset=claimed_token)

        for event in decoded_events:
            if event.event_type == HistoryEventType.RECEIVE and event.location_label == receiver and event.balance.amount == amount and claimed_token == event.asset:  # noqa: E501
                event.event_subtype = HistoryEventSubType.REWARD
                event.counterparty = CPT_VOTIUM
                event.notes = f'Receive {event.balance.amount} {event.asset.symbol} from votium bribe'  # noqa: E501

        return None, None

    # -- DecoderInterface methods

    def addresses_to_decoders(self) -> Dict[ChecksumEthAddress, Tuple[Any, ...]]:
        return {
            VOTIUM_CONTRACT: (self._decode_claim,),
        }

    def counterparties(self) -> List[str]:
        return [CPT_VOTIUM]

    def event_settings(self, pot: 'AccountingPot') -> Dict[str, TxEventSettings]:  # pylint: disable=unused-argument  # noqa: E501
        """Being defined at function call time is fine since this function is called only once"""
        return {
            get_tx_event_type_identifier(HistoryEventType.RECEIVE, HistoryEventSubType.REWARD, CPT_VOTIUM): TxEventSettings(  # noqa: E501
                taxable=True,
                count_entire_amount_spend=False,
                count_cost_basis_pnl=False,
                method='acquisition',
                take=1,
                multitake_treatment=None,
            ),
        }