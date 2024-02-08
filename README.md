# Resource Allocation
Reallocation / reassignment of items with limitations of constraints solved using linear programming in Python with PuLP

# Problem
Let:
- $x_{ij}$ be a binary decision variable where $x_{ij} = 1$ if item $i$ is assigned to category $j$, and $x_{ij} = 0$ otherwise.
- $p_i$ be the price of item $i$.
- $c_j$ be the price limit of category $j$.

The objective is to minimize or maximize a linear objective function. Since there is no specific objective mentioned in your problem statement, we can simply minimize the total cost.

The constraints are as follows:
1. Each item must be assigned to exactly one category:
$$\sum_{j} x_{ij} = 1 \quad \text{for all } i$$

2. The total price sum of items assigned to each category must not exceed the category limit:
$$\sum_{i} p_i \cdot x_{ij} \geq c_j \quad \text{for all } j$$

The LP formulation of this problem is:

$$
\text{Maximize} \quad \sum_{i} \sum_{j} p_i \cdot x_{ij}
$$

Subject to:
$$
\begin{align*}
& \sum_{j} x_{ij} = 1 \quad && \text{for all } i \\
& \sum_{i} p_i \cdot x_{ij} \leq c_j \quad && \text{for all } j \\
& x_{ij} \in \{0, 1\} \quad && \text{for all } i, j
\end{align*}
$$