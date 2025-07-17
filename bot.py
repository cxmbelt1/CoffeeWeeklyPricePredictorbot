import asyncio, aiohttp, json, datetime as dt, pathlib, logging, os

# -------------------- configuración --------------------
BOT_TOKEN   = "tokentoken" #colocar aqui el token
API_URL     = f"https://api.telegram.org/bot{BOT_TOKEN}"
CHATS_FILE  = pathlib.Path("chats.json")
SIGNAL_FILE = pathlib.Path("signals_hybrid.json")
UPDATE_INT  = 1.5

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
async def obtener_tasa_cop(session) -> float:
    url = "https://api.exchangerate.host/latest?base=USD&symbols=COP"
    try:
        async with session.get(url, timeout=10) as r:
            data = await r.json()
            return data.get("rates", {}).get("COP", 4000)
    except Exception as e:
        logging.error(f"Error al obtener tasa de cambio: {e}")
        return 4000  # Valor de respaldo
    
def html(t):                 # escapado mínimo para HTML
    return (str(t).replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;"))

# -------------------- señal --------------------
def load_signal(usd_to_cop: float) -> str | None:
    if not SIGNAL_FILE.exists():
        return None
    s = json.loads(SIGNAL_FILE.read_text())

    usd_per_lb = s["suggested_price"] / 100  # porque viene en USD/100 lb
    price_suggested_cop = usd_per_lb * usd_to_cop

    date  = html(s["date"])
    label = s["label"]
    ctx   = ("🚨 Se anticipa <b>caída</b>. Si necesita liquidez, considere vender."
             if label.startswith("⬇️") else
             "⚠️ Se anticipa <b>subida</b>. Esperar podría mejorar su precio."
             if label.startswith("⬆️") else
             "Mercado estable; venda según su plan habitual.")
    price_suggested_usd_per_lb = usd_per_lb

    msg = (
    f"<b>Pronóstico semanal – {date}</b>\n"
    f"• Precio hoy       : <code>{s['price_now'] / 100:.2f}</code> USD/lb\n"
    f"• Próx. lunes      : <code>{s['forecast'] / 100:.2f}</code> USD/lb\n"
    f"• Variación esperada: <code>{s['delta_pct']} %</code> {label}\n"
    f"• Precio sugerido  : <code>{price_suggested_cop:,.0f}</code> COP/lb\n"
    f"{ctx}\n\n"
    f"<i> Modelo {html(s['model'])}</i>\n"
    f"<b>La decisión de vender o retener es exclusivamente suya.</b>"
    )

    return msg

# -------------------- clase bot --------------------
class CoffeeBot:
    def __init__(self, token: str):
        self.api = f"https://api.telegram.org/bot{token}"
        self.chats = set(json.loads(CHATS_FILE.read_text())) if CHATS_FILE.exists() else set()
        self.offset = 0
        self.session = aiohttp.ClientSession()

    async def _post(self, method: str, **params):
        async with self.session.post(f"{self.api}/{method}", data=params) as r:
            data = await r.json()
            if not data.get("ok"):
                logging.error("API error %s: %s", method, data)
            return data

    async def send(self, chat_id: int, text: str, html_mode=False):
        await self._post(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode="HTML" if html_mode else None
        )

    async def handle_update(self, upd):
        if "message" not in upd:
            return
        msg = upd["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        # registrar chat
        if chat_id not in self.chats:
            self.chats.add(chat_id)
            CHATS_FILE.write_text(json.dumps(sorted(self.chats)))

        if text == "/start":
            await self.send(
                chat_id,
                "☕️ ¡Hola! Usa /signal para ver el pronóstico semanal y recibe alertas automáticas."
            )
        elif text == "/signal":
            tasa = await obtener_tasa_cop(self.session)
            sig = load_signal(tasa) or "Aún no hay señal calculada."
            await self.send(chat_id, sig, html_mode=True)

    # --------------- long polling -----------------
    async def polling(self):
        while True:
            try:
                params = {"timeout": 20, "offset": self.offset + 1}
                async with self.session.get(f"{self.api}/getUpdates", params=params, timeout=25) as r:
                    data = await r.json()
                for upd in data.get("result", []):
                    self.offset = max(self.offset, upd["update_id"])
                    await self.handle_update(upd)
            except Exception as e:
                logging.error("Polling error: %s", e)
                await asyncio.sleep(5)
            await asyncio.sleep(UPDATE_INT)

    # --------------- push semanal automático -----
    async def weekly_push(self):
        while True:
            now = dt.datetime.now()
            if now.weekday() == 1 and now.hour == 9 and now.minute == 30:  # martes 09:30
                tasa = await obtener_tasa_cop(self.session)  # obtiene la tasa de cambio del día
                sig = load_signal(tasa)  # usa esa tasa para calcular el precio sugerido en COP
                if sig:
                    for cid in self.chats:
                        await self.send(cid, sig, html_mode=True)
                await asyncio.sleep(60)
            await asyncio.sleep(20)

    async def run(self):
        await asyncio.gather(self.polling(), self.weekly_push())

# -------------------- main --------------------
async def main():
    if BOT_TOKEN.startswith("PEGA"):
        raise RuntimeError("⚠️  Debes configurar BOT_TOKEN")
    await CoffeeBot(BOT_TOKEN).run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Detenido por usuario.")
