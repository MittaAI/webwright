import matplotlib.pyplot as plt
import numpy as np

# Function to compute the Mandelbrot set
def mandelbrot(c, max_iter):
    z = c
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z*z + c
    return max_iter

# Generate the fractal
def generate_fractal(size):
    # Determine the plot boundaries
    x_min, x_max = -2.5, 1.5
    y_min, y_max = -2.0, 2.0

    width, height = (size*100, size*100)  # Increase resolution by multiplying size by 100
    x, y = np.linspace(x_min, x_max, width), np.linspace(y_min, y_max, height)
    fractal = np.zeros((width, height))

    for i in range(width):
        for j in range(height):
            fractal[i, j] = mandelbrot(complex(x[i], y[j]), 256)

    plt.imshow(fractal.T, extent=[x_min, x_max, y_min, y_max], cmap='hot')
    plt.colorbar()
    plt.title("Mandelbrot Fractal")
    plt.show()

# Generate a fractal of the given size
generate_fractal(20)
