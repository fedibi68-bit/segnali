"""
============================================================
  📡 SEGNALI 3 ALGORITMI — versione snella e AUTONOMA
  Watchlist propria (titoli_segnali.json), indipendente da Sentinella.
  Aggiungi/togli ticker da qui; poi "Cerca segnali di OGGI"
  mostra Momentum / Pullback / Compressione. Niente paper trading.
  Porta 8508.  Avvio: doppio clic su Avvia_Segnali.bat
============================================================
"""
import os, json
import streamlit as st
import pandas as pd
import backtest_engine as eng

st.set_page_config(page_title="Segnali 3 algoritmi", page_icon="📡", layout="wide")

TIT_FILE = "titoli_segnali.json"   # lista PROPRIA, separata da Sentinella
NOMI = {"momentum": "Momentum", "pullback": "Pullback", "compressione": "Compressione"}


def jload(path, default):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def jsave(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


titoli = jload(TIT_FILE, [])
base_algo = {t["ticker"]: t["algoritmo"] for t in titoli}

st.title("📡 Segnali di oggi — tutti e tre gli algoritmi")
st.caption("Versione snella e autonoma: ha la SUA watchlist (titoli_segnali.json), indipendente da Sentinella. "
           "Materiale didattico, non e' un consiglio finanziario.")

# ===== WATCHLIST PROPRIA =====
st.subheader("🗂️ La mia watchlist (di questa app)")
cc = st.columns([2, 1])
nuovo = cc[0].text_input("Aggiungi un titolo (ticker)", placeholder="es. NVDA, ENI.MI…",
                         key="seg_new").strip().upper()
if cc[1].button("➕ Aggiungi e classifica", use_container_width=True, key="seg_add") and nuovo:
    if nuovo in base_algo:
        st.warning(f"{nuovo} e' gia' nella watchlist.")
    else:
        try:
            with st.spinner(f"Misuro il carattere di {nuovo}… (un paio di secondi)"):
                info = eng.classifica_titolo(nuovo)
            titoli.append(info); jsave(TIT_FILE, titoli)
            st.success(f"{nuovo} aggiunto: {info['carattere']} (volatilita' {info['volatilita']}%) "
                       f"-> base {info['algoritmo']}.")
            st.rerun()
        except Exception as ex:
            st.error(f"Non riesco ad aggiungere {nuovo}: {ex}")

if not titoli:
    st.info("Watchlist vuota. Aggiungi qui sopra i titoli che vuoi sorvegliare: "
            "l'app li classifica da sola (calmo/nervoso) e li salva in titoli_segnali.json.")
    with st.expander("⬆️ …oppure importa una watchlist (.json) gia' pronta"):
        up0 = st.file_uploader("Importa una watchlist (.json)", type="json", key="seg_up0")
        if up0 is not None:
            try:
                nuovi = json.loads(up0.read().decode("utf-8"))
                if isinstance(nuovi, list) and all("ticker" in x and "algoritmo" in x for x in nuovi):
                    if st.button("✅ Conferma importazione", key="seg_imp0"):
                        jsave(TIT_FILE, nuovi)
                        st.success(f"Importati {len(nuovi)} titoli."); st.rerun()
                else:
                    st.error("File non valido (servono almeno 'ticker' e 'algoritmo').")
            except Exception as ex:
                st.error(f"File non leggibile: {ex}")
    st.stop()

calmi = [t for t in titoli if t["algoritmo"] == "momentum"]
nervosi = [t for t in titoli if t["algoritmo"] == "pullback"]
st.caption(f"{len(titoli)} titoli • 🟦 calmi: {len(calmi)} • 🟥 nervosi: {len(nervosi)} "
           f"• soglia: volatilita' >= {eng.SOGLIA_NERVOSO:.0f}% = nervoso")

with st.expander("👀 Vedi / gestisci la watchlist"):
    tab_wl = pd.DataFrame([{"Titolo": t["ticker"],
                            "Carattere": "🟥 nervoso" if t["algoritmo"] == "pullback" else "🟦 calmo",
                            "Volatilita'": f"{t['volatilita']}%", "Base": NOMI.get(t["algoritmo"], "?"),
                            "Prezzo (all'aggiunta)": t.get("prezzo", "—")}
                           for t in sorted(titoli, key=lambda x: x["volatilita"])])
    st.dataframe(tab_wl, use_container_width=True, hide_index=True)
    elimina = st.multiselect("Elimina titoli", [t["ticker"] for t in titoli], key="seg_del")
    if elimina and st.button("🗑️ Elimina selezionati", key="seg_delbtn"):
        jsave(TIT_FILE, [t for t in titoli if t["ticker"] not in elimina]); st.rerun()
    st.download_button("⬇️ Esporta questa watchlist", data=json.dumps(titoli, ensure_ascii=False, indent=2),
                       file_name="titoli_segnali.json", mime="application/json",
                       use_container_width=True, key="seg_exp")
    up = st.file_uploader("⬆️ Importa una watchlist (.json)", type="json", key="seg_up")
    if up is not None:
        try:
            nuovi = json.loads(up.read().decode("utf-8"))
            if isinstance(nuovi, list) and all("ticker" in x and "algoritmo" in x for x in nuovi):
                if st.button("✅ Conferma: sostituisci la watchlist", key="seg_impok"):
                    jsave(TIT_FILE, nuovi)
                    st.success(f"Importati {len(nuovi)} titoli."); st.rerun()
            else:
                st.error("File non valido (servono almeno 'ticker' e 'algoritmo').")
        except Exception as ex:
            st.error(f"File non leggibile: {ex}")

st.divider()

# ===== SCANSIONE SEGNALI =====
st.subheader("📡 Segnali di oggi")
c1, c2 = st.columns([1, 2])
cerca = c1.button("🔄 Cerca segnali di OGGI", type="primary", use_container_width=True, key="seg_scan")
mostra_tutti = c2.checkbox("Mostra anche i titoli senza segnale", value=False, key="seg_all")

if cerca:
    with st.spinner("Controllo Momentum, Pullback e Compressione su ogni titolo…"):
        try:
            st.session_state["scan3_solo"] = eng.segnali_oggi_multi([t["ticker"] for t in titoli], periodo="2y")
        except Exception as ex:
            st.error(f"Problema: {ex}")

res = st.session_state.get("scan3_solo")
if res:
    st.caption(f"Dati al {res['data_aggiornamento']}.")
    righe = res["righe"]
    con_segnale = [r for r in righe if r["qualcuno"]]
    da_mostrare = righe if mostra_tutti else con_segnale

    if not con_segnale and not mostra_tutti:
        st.info("🟢 Nessun segnale oggi su nessuno dei tre algoritmi. Si aspetta.")
    else:
        if con_segnale:
            n_conf = sum(1 for r in con_segnale
                         if (bool(r["momentum"]) + bool(r["pullback"]) + bool(r["compressione"])) >= 2)
            st.success(f"⚡ Titoli con almeno un segnale oggi: {len(con_segnale)}"
                       + (f" — di cui in confluenza (2+): {n_conf}" if n_conf else ""))
        spunta = lambda b: "✅" if b else "—"

        def n_attivi(r):
            return int(bool(r["momentum"])) + int(bool(r["pullback"])) + int(bool(r["compressione"]))

        # confluenze (2+) in cima, poi per numero di algoritmi attivi
        da_mostrare = sorted(da_mostrare, key=lambda r: -n_attivi(r))

        tab = pd.DataFrame([{
            "": "🔗" if n_attivi(r) >= 2 else "",
            "Titolo": r["ticker"], "Prezzo": r["prezzo"],
            "Base": NOMI.get(base_algo.get(r["ticker"], ""), "?"),
            "Momentum": spunta(r["momentum"]), "Pullback": spunta(r["pullback"]),
            "Compressione": spunta(r["compressione"]), "Stop sugg.": r["stop_suggerito"],
        } for r in da_mostrare])

        # evidenzia di verde tenue le righe in confluenza (2+ algoritmi)
        def evidenzia(row):
            conf = row[""] == "🔗"
            return ["background-color: rgba(34,197,94,0.18); font-weight:600" if conf else "" for _ in row]

        try:
            styled = tab.style.apply(evidenzia, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True)
        except Exception:
            # se lo styling non è disponibile, mostra comunque la tabella semplice
            st.dataframe(tab, use_container_width=True, hide_index=True)

        st.caption("🔗 = confluenza (2+ algoritmi accesi): righe verdi in cima. "
                   "'Base' = l'algoritmo naturale del titolo (dalla volatilita'). "
                   "La Compressione si accende solo nei giorni di compressione. ✅ = segnale attivo oggi.")
    if res["falliti"]:
        st.caption("Non scaricati: " + ", ".join(res["falliti"]) + ".")
else:
    st.info("Premi «Cerca segnali di OGGI» per scansionare la tua watchlist.")

st.divider()
st.caption("Watchlist propria in titoli_segnali.json (separata da Sentinella). "
           "Lo strumento segnala, la decisione resta tua.")
