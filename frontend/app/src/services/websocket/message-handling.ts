import { Severity } from '@rotki/common/lib/messages';
import i18n from '@/i18n';
import {
  BalanceSnapshotError,
  EthereumTransactionQueryData,
  SocketMessageType,
  WebsocketMessage
} from '@/services/websocket/messages';
import { useTransactions } from '@/store/history';
import { useNotifications } from '@/store/notifications';

export async function handleSnapshotError(
  message: WebsocketMessage<SocketMessageType>
) {
  const data = BalanceSnapshotError.parse(message.data);
  const { notify } = useNotifications();
  notify({
    title: i18n.t('notification_messages.snapshot_failed.title').toString(),
    message: i18n
      .t('notification_messages.snapshot_failed.message', data)
      .toString(),
    display: true
  });
}

export async function handleEthereumTransactionStatus(
  message: WebsocketMessage<SocketMessageType>
) {
  const data = EthereumTransactionQueryData.parse(message.data);
  const { setQueryStatus } = useTransactions();
  setQueryStatus(data);
}

export async function handleLegacyMessage(message: string, isWarning: boolean) {
  const { notify } = useNotifications();
  notify({
    title: i18n.t('notification_messages.backend.title').toString(),
    message: message,
    display: !isWarning,
    severity: isWarning ? Severity.WARNING : Severity.ERROR
  });
}
