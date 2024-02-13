import sys
import pandas as pd
from collections import defaultdict
import time
import json
import pulp
from datetime import date
import pyodbc
from dotenv import load_dotenv
import os

pulp.LpSolverDefault.msg = 1

def assign_items_to_categories(items, categories, category_limits) -> dict[str, list]:
    """
    Linear Programming - Resource Allocation Problem using PuLP

    Let:
    - \( x_{ij} \) be a binary decision variable where \( x_{ij} = 1 \) if item \( i \) is assigned to category \( j \), and \( x_{ij} = 0 \) otherwise.
    - \( p_i \) be the price of item \( i \).
    - \( c_j \) be the price limit of category \( j \).

    The objective is to minimize or maximize a linear objective function. Since there is no specific objective mentioned in your problem statement, we can simply maximize the total cost.

    The constraints are as follows:
    1. Each item must be assigned to exactly one category:
    \[ \sum_{j} x_{ij} = 1 \quad \text{for all } i \]

    2. The total price sum of items assigned to each category must not exceed the category limit:
    \[ \sum_{i} p_i \cdot x_{ij} \geq c_j \quad \text{for all } j \]

    The LP formulation of this problem is:

    \[
    \text{Maximize} \quad \sum_{i} \sum_{j} p_i \cdot x_{ij}
    \]

    Subject to:
    \[
    \begin{align*}
    & \sum_{j} x_{ij} = 1 \quad && \text{for all } i \\
    & \sum_{i} p_i \cdot x_{ij} \leq c_j \quad && \text{for all } j \\
    & x_{ij} \in \{0, 1\} \quad && \text{for all } i, j
    \end{align*}
    \]
    """
    # OFFICIAL ALGORITHM
    n = len(items)
    m = len(categories)
    model = pulp.LpProblem("Assign_Items_to_Categories", sense=pulp.LpMaximize)

    # Define decision variables
    x = pulp.LpVariable.dicts("x", ((i, j) for i in range(n) for j in range(m)), cat='Binary')
    

    # Objective function
    # model += pulp.lpSum((items[i]["price"] * x[(i, j)] for i in range(n) for j in range(m)))

    # Constraints
    for i in range(n):
        model += pulp.lpSum(x[(i, j)] for j in range(m)) == 1

    for j in range(m):
        model += pulp.lpSum(items[i]["price"] * x[(i, j)] for i in range(n)) >= category_limits[categories[j]]

    # Solve the problem
    model.solve()
    # Extract the solution
    assignment_result = {category: [] for category in categories}
    for i in range(n):
        valid = False
        for j in range(m):
            if pulp.value(x[(i, j)]) == 1:
                valid = True
                assignment_result[categories[j]].append(items[i])
        if not valid:
            print('invalid item:', items[i])
    return assignment_result


if __name__ == '__main__':
    load_dotenv()
    (pathname, *cmd_args) = sys.argv
    
    if len(cmd_args) != 2:
        raise SystemExit('Please provide 2 arguments: the file path to REPO items and file path to REPO total balance')
    
    start = time.time()

    # Get the content of the excel cusip file (on the first sheet)
    dfs_items = pd.read_excel(cmd_args[0], sheet_name=0)
    # Drop any rows that contains missing values
    dfs_items = dfs_items.dropna(subset=['CUSIP', 'Market Value'])
    # Get the content of the excel categories total balance file (on the first sheet)
    dfs_categories = pd.read_excel(cmd_args[1], sheet_name=0)
    # Drop any rows that contains missing values
    dfs_categories = dfs_categories.dropna()
    categories = dfs_categories['Title'].values
    repo_items = []
    category_limits = defaultdict(float)
    total_market_value, total_balance = 0, 0
    # category_limits = dfs_categories['Current DDA Balance'].values
    for i, (cusip, m_value) in dfs_items[['CUSIP', 'Market Value']].iterrows():
        repo_items.append({
            'cusip': cusip,
            'price': m_value,
        })
        total_market_value += m_value

    for i, (title, balance) in dfs_categories[['Title', 'Current DDA Balance']].iterrows():
        category_limits[title] = balance
        total_balance += balance

    
    # if total market value is smaller than total balance, then raise an error
    if total_market_value < total_balance:
        raise SystemError("Total market value of all items is less than total DDA balance of all client! Please add more items.")

    result = assign_items_to_categories(repo_items, categories, category_limits) 
   
    # write result to a JSON file (with price)
    with open(f'repo_reassignment_price_{date.today().strftime("%m%d%Y")}.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    # write result to a txt file (without price)
    result = {cat: [item['cusip'] for item in result[cat]] for cat in result}

    connectionString = f'''
    DRIVER={"{SQL Server Native Client 11.0}"};
    SERVER=FFS-AZ-PDWT02;
    DATABASE=BIDW;
    UID={os.environ['SQL_USER']};
    PWD={os.environ['SQL_PASSWORD']};
    '''

    db = pyodbc.connect(connectionString)

    # Check if the cusip ID is present
    cusip_exist = '''
    SELECT COUNT(*)
    FROM [dbo].t_RepoReassignment
    WHERE CUSIP_ID=?
    '''
    # Update if the cusip ID is present
    cusip_update = '''
    UPDATE [dbo].t_RepoReassignment
    SET Customer_Name=?
    WHERE CUSIP_ID=?
    '''
    # Insert if the cusip ID is not present
    cusip_insert = '''
    INSERT INTO [dbo].t_RepoReassignment (CUSIP_ID, Customer_Name)
    VALUES (?, ?)
    '''
    with db.cursor() as db_cursor:
        for cat in result:
            for cusip in result[cat]:
                
                if db_cursor.execute(cusip_exist, cusip).fetchone()[0]:
                    # Update result
                    db_cursor.execute(cusip_update, cat, cusip)
                else:
                    # Insert result
                    db_cursor.execute(cusip_insert, cusip, cat)
    db.close()
    end = time.time()

    print(f'Time to execute: {(end - start):.2f} seconds')

