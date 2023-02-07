
# Filtering/Delete rows

    df_out[pd.isnull(df_out['Desc'])]
    df_out[df_out['enUS'].str.contains("text")]
    df.drop(df[ df['Desc'].str.len() == 0 ].index, inplace=True)

# Columns

    df.drop(columns=['B', 'C'])

# New df

    df.sort_values(by=['col1'])

    df2 = df[list_columns].copy()
    df2 = df.filter(list_columns, axis=1)
    df2.index += 1

# dtype

    df = df.convert_dtypes()
    df.dtypes             # hide if too many columns
    df.info(verbose=True) # print all columns & Non-Null Count

# Modify cell values

    #  <NA> -> ""
    df[col] = df[col].apply(lambda x: "" if x is pd.NA else x)

    df[col] = df[col1] + df[col2]

    # re.sub()
    df["col"] = df['col'].str.replace(r'/{2,}', '', regex=True).astype('str')

# load .json

    # UTF8 with BOM
    df = pd.DataFrame(json.load(codecs.open(json_file, 'r', 'utf-8-sig')))

# Join

    df = df_Runes_valid.merge(df_Runes_trans, left_on='Name', right_on='Key', how='left')

# Excel

    df.to_excel("file.xlsx", index=False)

    import xlwings
    xlwings.view(df) # auto open

multi df to file: pandas_N_excel.ipynb

https://xlsxwriter.readthedocs.io/working_with_autofilters.html

    # (0, 0, 10, 3) = ('A1:D11')
    autofilter(first_row, first_col, last_row, last_col)
