import pandas as pd
url = "https://www.datos.gov.co/resource/g4t8-zkc3.csv?$limit=5"
df = pd.read_csv(url)
print(df.columns.tolist())
print(df.head().to_string())
