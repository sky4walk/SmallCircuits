def kronecker_product(A, B):
    m, n = len(A), len(A[0])  # Groesse von A
    p, q = len(B), len(B[0])  # Groesse von B

    # Initialisiere eine leere Ergebnismatrix mit der richtigen Groesse
    C = [[0] * (n * q) for _ in range(m * p)]

    for i in range(m):
        for j in range(n):
            for k in range(p):
                for l in range(q):
                    x = i * p + k
                    y = j * q + l
                    C[x][y] = A[i][j] * B[k][l]
                    print("(",x,",",y,") ",A[i][j], "*", B[k][l])

    return C

# Beispielmatrizen
A = [[1, 2],
     [3, 4]]

B = [[0, 5],
     [6, 7]]

# Berechnung des Kronecker-Produkts
result = kronecker_product(A, B)

# Ergebnis ausgeben
for row in result:
    print(row)