# utils/hidrologia.py

import pandas as pd

def obter_afluencia_incremental_patu() -> dict:
    try:
        df = pd.read_excel("data/aflu_incr_Patu_10.xlsx", sheet_name="Sheet 1")

        df_long = df.melt(id_vars=df.columns[0], var_name="mes", value_name="afluencia_hm3")
        df_long.rename(columns={df.columns[0]: "ano"}, inplace=True)

        mes_map = {
            "JAN": "01", "FEV": "02", "MAR": "03", "ABR": "04", "MAI": "05", "JUN": "06",
            "JUL": "07", "AGO": "08", "SET": "09", "OUT": "10", "NOV": "11", "DEZ": "12"
        }
        df_long["mes_num"] = df_long["mes"].map(mes_map)
        df_long["data"] = pd.to_datetime(df_long["ano"].astype(str) + "-" + df_long["mes_num"])

        df_long = df_long.dropna(subset=["afluencia_hm3"])
        df_long = df_long.sort_values("data")

        ultimo = df_long.iloc[-1]
        return {
            "data": ultimo["data"].strftime('%Y-%m-%d'),
            "afluencia_hm3": round(float(ultimo["afluencia_hm3"]), 4),
            "afluencia_m3s_aprox": round((ultimo["afluencia_hm3"] * 1_000_000) / (30 * 24 * 3600), 2)
        }
    except Exception as e:
        return {"error": f"Erro ao processar afluência incremental: {e}"}
