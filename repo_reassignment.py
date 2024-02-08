import sys
import pandas as pd
import numpy as np
from scipy.optimize import linprog
from collections import defaultdict
import time
import json
import pulp

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
    model.writeLP('model.lp')
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
    (pathname, *cmd_args) = sys.argv
    
    if len(cmd_args) != 2:
        raise SystemExit('Please provide 2 arguments: the file path to REPO items and file path to REPO total balance')
    
    start = time.time()

    # Get the content of the excel cusip file (on the first sheet)
    dfs_items = pd.read_excel(cmd_args[0], sheet_name=0)
    # Get the content of the excel categories total balance file (on the first sheet)
    dfs_categories = pd.read_excel(cmd_args[1], sheet_name=0)
    categories = dfs_categories['Title'].values
    repo_items = []
    category_limits = defaultdict(float)
    # category_limits = dfs_categories['Current DDA Balance'].values
    for i, (cusip, m_value) in dfs_items[['CUSIP', 'Market Value']].iterrows():
        repo_items.append({
            'cusip': cusip,
            'price': m_value,
        })

    for i, (title, balance) in dfs_categories[['Title', 'Current DDA Balance']].iterrows():
        category_limits[title] = balance

    result = assign_items_to_categories(repo_items, categories, category_limits) 
   
    # write result to a JSON file (with price)
    with open('result_price.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

     # write result to a JSON file (without price)
    result = {cat: [item['cusip'] for item in result[cat]] for cat in result}
    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    

    end = time.time()

    print(f'Time to execute: {(end - start):.2f} seconds')
