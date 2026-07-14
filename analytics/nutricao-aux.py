# Esse arquivo é um auxiliar de nutricao.qmd, pois 
# o meu LSP não estava funcionando em arquivos quarto.

from typing import cast

from google.cloud import bigquery
import pandas as pd

#---

client = bigquery.Client(project="atlas-computing-359718")

query = """
SELECT *
FROM `atlas-computing-359718.bronze.raw_notas_nutricao`
LIMIT 100
"""

df = cast(pd.DataFrame, client.query(query).to_dataframe())

print(df.columns)

df = df[df["foi_feito"] == True][["data_referencia", "eh_meta", "descricao"]]

#---

# 0. Remove '[]'

df["descricao"] = df["descricao"].str.replace(r"[|]", "", regex=True)

# 1. Split description by '+' to get each item

df["itens"] = df["descricao"].str.split("+")
exploded = df.explode("itens").reset_index(drop=True)
exploded["itens"] = exploded["itens"].str.strip().fillna("").astype(object)

# 2. Split it further by 'com' whenever it is followed by a number

exploded["tem_com_com_digito"] = exploded["itens"].str.contains(r"\s+com\s+\d+", regex=True)

mask = exploded["tem_com_com_digito"]
exploded.loc[mask, "itens"] = exploded.loc[mask, "itens"].str.split("com")

exploded = exploded.explode("itens").reset_index(drop=True)
exploded["itens"] = exploded["itens"].str.strip()

exploded.head(50)

#exploded.head()

full = exploded["itens"].str.extract(
    r"(?P<quantidade>\d+(?:\.\d+)?)\s*"
	r"(?P<unidade>g|ml|kg|l|xicara|xicaras|copo|copos|fatia|fatias|scoop)\s+de\s+"
	r"(?P<alimento>.+)"
)

missing = full["alimento"].isna()
fallback = exploded.loc[missing, "itens"].str.extract(
    r"(?P<quantidade>\d+(?:\.\d+)?)\s+(?P<alimento>.+)"
)

fallback["unidade"] = "un"

full.loc[missing, ["quantidade", "unidade", "alimento"]] = fallback[
    ["quantidade", "unidade", "alimento"]
]

result = pd.concat([exploded, full], axis=1)

result.head(50)
