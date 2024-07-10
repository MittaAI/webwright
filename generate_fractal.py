import matplotlib.pyplot as plt
import numpy as np

# Function to plot the Mandelbrot set
def mandelbrot(c, max_iter):
    z = c
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z*z + c
    return max_iter

# Generate the fractal
size = 20
x = np.linspace(-2.0, 1.0, size * 1000)
y = np.linspace(-1.5, 1.5, size * 1000)
X, Y = np.meshgrid(x, y)
C = X + 1j * Y

# Apply the mandelbrot function to each point in the grid
mandelbrot_set = np.array([[mandelbrot(c, 256) for c in row] for row in C])

# Plot the fractal
plt.figure(figsize=(10, 10))
plt.imshow(mandelbrot_set, extent=(-2, 1, -1.5, 1.5), cmap='hot')
plt.colorbar()
plt.title('Mandelbrot Set')
plt.xlabel('Re')
plt.ylabel('Im')
plt.show()
