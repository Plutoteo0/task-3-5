import pandas as pd
from data_processing import read_books, clean_books, DATA_PATH

books = clean_books(read_books(DATA_PATH))
df = pd.DataFrame(books)

df["usd"] = df["price"].where(df['currency'] != 'EUR', df["price"] * 1.2)

check = df.groupby("year")["usd"].agg(["size", "mean"])
check["mean"] = check["mean"].round(2)
print(check.loc[[1871, 2004]])