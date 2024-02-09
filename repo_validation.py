import json
import sys
import pandas as pd
from datetime import date

if __name__ == '__main__':
    (pathname, *cmd_args) = sys.argv
        
    if len(cmd_args) != 1:
        raise SystemExit('Please provide 1 argument: the file path to REPO total balance')
    

    df_categories = pd.read_excel(cmd_args[0], sheet_name=0)
    # Load the result JSON file
    result = None
    with open(f'repo_reassignment_price_{date.today().strftime("%m%d%Y")}.json', 'r', encoding='utf-8') as f:
        result = json.load(f)

    category_assignment = {}
    df_categories = df_categories[['Title', 'Current DDA Balance']]

    for cat in result:
        category_assignment[cat] = sum([result[cat][i]['price'] for i in range(len(result[cat]))])
        df_categories.loc[df_categories.index[df_categories['Title'] == cat], 'Total Market Value'] = category_assignment[cat]
        df_categories.loc[df_categories.index[df_categories['Title'] == cat], 'Is Correct?'] = df_categories.loc[df_categories.index[df_categories['Title'] == cat], 'Current DDA Balance'] <= category_assignment[cat]

    df_categories.to_excel('repo_reassignment_result.xlsx')
    
    

    