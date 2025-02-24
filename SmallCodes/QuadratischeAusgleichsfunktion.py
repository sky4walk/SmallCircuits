import matplotlib.pyplot as plt

def transpose(matrix):
    return [[row[i] for row in matrix] for i in range(len(matrix[0]))]

def mat_mult(A, B):
    return [[sum(a * b for a, b in zip(A_row, B_col)) for B_col in zip(*B)] for A_row in A]

def inverse_3x3(matrix):
    det = (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) -
           matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0]) +
           matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))
    
    if det == 0:
        raise ValueError("Matrix ist nicht invertierbar")
    
    inv_det = 1 / det
    adjugate = [[matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1],
                 matrix[0][2] * matrix[2][1] - matrix[0][1] * matrix[2][2],
                 matrix[0][1] * matrix[1][2] - matrix[0][2] * matrix[1][1]],
                [matrix[1][2] * matrix[2][0] - matrix[1][0] * matrix[2][2],
                 matrix[0][0] * matrix[2][2] - matrix[0][2] * matrix[2][0],
                 matrix[0][2] * matrix[1][0] - matrix[0][0] * matrix[1][2]],
                [matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0],
                 matrix[0][1] * matrix[2][0] - matrix[0][0] * matrix[2][1],
                 matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]]]
    
    return [[inv_det * adjugate[i][j] for j in range(3)] for i in range(3)]

def lstsq_custom(A, b):
    A_T = transpose(A)
    A_T_A = mat_mult(A_T, A)
    A_T_b = mat_mult(A_T, [[val] for val in b])
    
    inv_A_T_A = inverse_3x3(A_T_A)
    x = mat_mult(inv_A_T_A, A_T_b)
    return [val[0] for val in x]

def quadratic_fit(x_values, y_values):
    A = [[x**2, x, 1] for x in x_values]
    coeffs = lstsq_custom(A, y_values)
    
    def poly_func(x):
        return coeffs[0] * x**2 + coeffs[1] * x + coeffs[2]
    
    return poly_func, coeffs

# Beispielwerte
x_data = [1, 2, 3, 4, 5]
#y_data = [2, 5, 10, 17, 26]
y_data = [2, 5.5, 9.5, 16, 27]

quad_func, coefficients = quadratic_fit(x_data, y_data)
print("Koeffizienten (a, b, c):", coefficients)

x_plot = [x / 10.0 for x in range(min(x_data) * 10, max(x_data) * 10 + 1)]
y_plot = [quad_func(x) for x in x_plot]

print(x_plot)
print(y_plot)

plt.scatter(x_data, y_data, color='red', label='Datenpunkte')
plt.plot(x_plot, y_plot, label='Quadratische Ausgleichsfunktion', color='blue')
plt.legend()
plt.xlabel('x')
plt.ylabel('y')
plt.title('Quadratische Regression')
plt.grid()
plt.show()
