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

# Drawing the Mandelbrot set
def draw_mandelbrot(width, height, x_min, x_max, y_min, y_max, max_iter, filename):
    re = np.linspace(x_min, x_max, width)
    im = np.linspace(y_min, y_max, height)
    X = np.empty((width, height))
    
    for i in range(width):
        for j in range(height):
            c = re[i] + 1j * im[j]
            X[i, j] = mandelbrot(c, max_iter)

    plt.imshow(X.T, extent=[x_min, x_max, y_min, y_max], cmap='inferno')
    plt.colorbar()
    plt.savefig(filename)
    plt.show()

if __name__ == "__main__":
    draw_mandelbrot(width=800, height=800, x_min=-2.0, x_max=1.0, y_min=-1.5, y_max=1.5, max_iter=256, filename="mandelbrot.png")
