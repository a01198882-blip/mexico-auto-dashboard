from pathlib import Path
import zipfile
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
ZIP_PATH = BASE_DIR / "data" / "conjunto_de_datos_raiavl_mensual_venta_csv.zip"
OUTPUT_CSV = BASE_DIR / "data" / "cleaned_ventas.csv"


def run_pipeline(zip_path: Path = ZIP_PATH, output_csv: Path = OUTPUT_CSV) -> pd.DataFrame:
    # 1. Load 2016-2026 monthly sales + catalogs directly from the INEGI ZIP
    with zipfile.ZipFile(zip_path, "r") as z:
        sales_frames = []
        for year in range(2016, 2027):
            file_path = f"conjunto_de_datos/raiavl_venta_mensual_tr_cifra_{year}.csv"
            with z.open(file_path) as f:
                sales_frames.append(pd.read_csv(f))
        df = pd.concat(sales_frames, ignore_index=True)

        with z.open("catalogos/tc_pais_origen.csv") as f:
            cat_pais = pd.read_csv(f)
        with z.open("catalogos/tc_mes.csv") as f:
            cat_mes = pd.read_csv(f)

    # 2. Merge catalogs & build proper monthly dates
    df = df.merge(cat_pais, on="ID_PAIS_ORIGEN", how="left")
    df = df.merge(cat_mes, on="ID_MES", how="left")
    df["FECHA"] = pd.to_datetime(dict(year=df["ANIO"], month=df["ID_MES"], day=1))

    # 3. Harmonize brand names and corporate groups
    brand_fixes = {
        "JETOUR": "Jetour",
        "Jetour Soueast": "Jetour",
    }
    df["MARCA_CLEAN"] = df["MARCA"].replace(brand_fixes)

    corporate_groups = {
        "Chrysler": "Stellantis",
        "Fiat": "Stellantis",
        "Peugeot": "Stellantis",
        "Alfa Romeo": "Stellantis",
        "Leapmotor": "Stellantis (JV)",
        "Volkswagen": "Volkswagen Group",
        "Audi": "Volkswagen Group",
        "SEAT": "Volkswagen Group",
        "Porsche": "Volkswagen Group",
        "Bentley": "Volkswagen Group",
        "General Motors": "General Motors",
        "Ford Motor": "Ford Motor",
        "Lincoln": "Ford Motor",
        "Nissan": "Renault-Nissan-Mitsubishi",
        "Infiniti": "Renault-Nissan-Mitsubishi",
        "Renault": "Renault-Nissan-Mitsubishi",
        "Mitsubishi": "Renault-Nissan-Mitsubishi",
        "Toyota": "Toyota Group",
        "Lexus": "Toyota Group",
        "Honda": "Honda Group",
        "Acura": "Honda Group",
        "Hyundai": "Hyundai-KIA",
        "KIA": "Hyundai-KIA",
        "BMW": "BMW Group",
        "Mini": "BMW Group",
        "Mercedes Benz": "Mercedes-Benz",
        "Smart": "Mercedes-Benz",
        "Chirey": "Chirey Group",
        "Omoda": "Chirey Group",
        "Geely": "Geely Group",
        "Zeekr": "Geely Group",
        "Lynk&Co": "Geely Group",
        "Volvo": "Geely Group",
    }
    df["GRUPO_CORPORATIVO"] = df["MARCA_CLEAN"].map(corporate_groups).fillna(df["MARCA_CLEAN"])

    # 4. Distinguish Chinese brands vs. legacy brands & manufacturing origin
    chinese_brands = {
        "Changan", "Chirey", "Foton", "GAC", "Geely", "Great Wall Motor",
        "JAC", "Jetour", "Leapmotor", "Lynk&Co", "MG Motor", "MOTORNATION",
        "Omoda", "Zeekr",
    }
    df["TIPO_MARCA"] = np.where(
        df["MARCA_CLEAN"].isin(chinese_brands),
        "Chinese Brand",
        "Legacy / Non-Chinese Brand",
    )

    def map_origin_block(country: str) -> str:
        if country == "México":
            return "Mexico (Domestic Assembly)"
        if country == "China":
            return "China (Imported)"
        if country in {"Estados Unidos", "Canadá"}:
            return "USA & Canada (USMCA)"
        if country in {"Japón", "Corea del Sur", "Tailandia", "India", "Indonesia"}:
            return "Rest of Asia"
        if country in {"Brasil", "Argentina", "Colombia"}:
            return "South America (ACE 55)"
        return "Europe & Other"

    df["BLOQUE_ORIGEN"] = df["DESC_PAIS_ORIGEN"].apply(map_origin_block)

    # 5. Classify trade / tariff regime (Jan 2026 non-FTA tariff hike)
    fta_countries = {
        "México", "Estados Unidos", "Canadá", "Brasil", "Argentina", "Colombia",
        "Japón", "Alemania", "España", "Francia", "Italia", "Reino Unido",
        "Suecia", "Austria", "Bélgica", "Eslovaquia", "Hungría", "Países Bajos",
        "Polonia", "República Checa", "Finlandia", "Serbia", "Turquía",
    }
    df["REGIMEN_ARANCELARIO"] = np.where(
        df["DESC_PAIS_ORIGEN"] == "México",
        "Domestic (0% Tariff)",
        np.where(
            df["DESC_PAIS_ORIGEN"].isin(fta_countries),
            "FTA / ACE Preferential Import",
            "Non-FTA Import (2026 Tariff Target)",
        ),
    )

    # 6. Flag consistent 10-year reporting panel to isolate entry/exit artifacts
    total_months = df["FECHA"].nunique()
    months_per_brand = df.groupby("MARCA_CLEAN")["FECHA"].nunique()
    consistent_brands = set(months_per_brand[months_per_brand == total_months].index)
    df["PANEL_CONSISTENTE_10Y"] = df["MARCA_CLEAN"].isin(consistent_brands)

    # 7. Export clean table
    keep_cols = [
        "FECHA", "ANIO", "ID_MES", "DESCRIPCION_MES",
        "MARCA", "MARCA_CLEAN", "GRUPO_CORPORATIVO", "TIPO_MARCA",
        "MODELO", "TIPO", "SEGMENTO",
        "ORIGEN", "DESC_PAIS_ORIGEN", "BLOQUE_ORIGEN", "REGIMEN_ARANCELARIO",
        "PANEL_CONSISTENTE_10Y", "ESTATUS", "UNI_VEH",
    ]
    df_clean = df[keep_cols].sort_values(["FECHA", "MARCA_CLEAN", "MODELO"]).reset_index(drop=True)
    df_clean.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Success! Saved {len(df_clean):,} rows to {output_csv}")
    return df_clean


if __name__ == "__main__":
    run_pipeline()