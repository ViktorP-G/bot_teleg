import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Callable
from .parser import get_weather_by_day, get_latest_days


class TelegramBot:
    _update_timeout: int = 15
    _session = None
    _token: str = ""
    _handlers: list[Callable[[dict], bool]] = None
    _offset = -1

    def __init__(self, token, update_timeout: int = 15):
        self._token = token
        self._update_timeout = update_timeout
        self._handlers = list()

    def get_handle_url(self, handle_name):
        return f"https://api.telegram.org/bot{self._token}/{handle_name}"

    def _get_session(self):
        self._session = requests.session()
        retry_strategy = Retry(
            status_forcelist=[429, 500, 502, 503, 504],
            total=3,
            allowed_methods=["GET", "POST"]
        )

        self._session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

        return self._session

    @staticmethod
    def _extract_user_and_text_from_message(msg) -> tuple[str, str]:
        _from = msg.get('from')
        if not _from:
            return '', ''
        username = _from.get('username')
        if not username:
            return '', ''

        text = msg.get('text', '')

        return username, text

    def run(self):
        with self._get_session() as session:
            while True:
                updates = self._fetch_updates()

                for update in updates:
                    self._handle_update(update)

    def _fetch_updates(self) -> list:
        response = self._session.post(
            self.get_handle_url("getUpdates"),
            json={
                "offset": self._offset + 1,
                "timeout": self._update_timeout

            },
            timeout=self._update_timeout + 1
        )

        response.raise_for_status()

        data = response.json()
        if data['ok']:
            return data['result']
            raise ValueError("Unexpected format for response: 'ok' field is not true ")

    def _handle_update(self, update: dict):
        message = update.get('message')
        if not message:
            return

        text = message.get('text', '').strip()
        chat_id = message['chat']['id']
        self._offset = max(self._offset, update['update_id'])

        if text == '/start':
            self._send_message(
                "Привет! 🌤️\n"
                "Я показываю погоду из собранных данных.\n\n"
                "Чтобы получить погоду за конкретный день, напишите:\n"
                "<code>/day ГГГГ-ММ-ДД</code>\n"
                "Например: <code>/day 2025-09-23</code>\n\n"
                "Чтобы увидеть последние данные — напишите:\n"
                "<code>/all</code>",
                chat_id
            )
        elif text == '/all':
            records = get_latest_days(days=7)
            self._send_message(self._format_records_with_date(records), chat_id)
        elif text.startswith('/day '):
            try:
                date_part = text.split(' ', 1)[1].strip()
                if len(date_part) == 10 and date_part[4] == '-' and date_part[7] == '-':
                    records = get_weather_by_day(date_part)
                    self._send_message(self._format_records_for_day(records), chat_id)
                else:
                    self._send_message("Неверный формат даты. Пример: /day 2025-09-23", chat_id)
            except Exception:
                self._send_message("Ошибка обработки команды. Используй /day YYYY-MM-DD", chat_id)
        else:
            self._send_message("Неизвестная команда. Напиши /start", chat_id)

    def _send_message(self, text, chat_id):
        response = self._session.post(
            self.get_handle_url("sendMessage"),
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
        )
        response.raise_for_status()

    def _format_records_with_date(self, records: list) -> str:
        if not records:
            return "Данные не найдены."

        from collections import defaultdict
        grouped = defaultdict(list)
        for r in records:
            grouped[r["date_str"]].append(r)

        sorted_dates = sorted(grouped.keys(), reverse=True)

        lines = []
        for date in sorted_dates:
            lines.append(f"📆 <b>{date}</b>")
            for r in grouped[date]:
                lines.append(
                    f"🕗 {r['time_str']} — {r['Температура']}°C, "
                    f"ветер {r['Ветер']} м/с, давл. {r['Давление']} мм, влажность {r['Влажность']}%"
                )
            lines.append("")

        return "\n".join(lines).strip()

    def _format_records_for_day(self, records: list) -> str:
        if not records:
            return "Данные не найдены."
        lines = []
        for r in records:
            lines.append(
                f"🕗 {r['time_str']} — {r['Температура']}°C\n"
                f"💨 Ветер: {r['Ветер']} м/с\n"
                f"🔽 Давление: {r['Давление']} мм\n"
                f"💧 Влажность: {r['Влажность']}%\n"
            )
        return "\n".join(lines)
