import matplotlib.pyplot as plt
import numpy as np

# function to compute the mandelbrot set
def mandelbrot(c, max_iter):
    z = c
    for n in range(max_iter):
        if abs(z) > 2:
            return n
        z = z*z + c
    return max_iter

# define the dimensions and resolution of the plot
xmin, xmax, ymin, ymax = -2.0, 1.0, -1.5, 1.5
width, height = 800, 800
max_iter = 255

# create an array to store the fractal
bitmap = np.zeros((height, width), dtype=np.uint8)

# create the fractal
for x in range(width):
    for y in range(height):
        real = xmin + (x / width) * (xmax - xmin)
        imag = ymin + (y / height) * (ymax - ymin)
        c = complex(real, imag)
        color = mandelbrot(c, max_iter)
        bitmap[y, x] = color

# plot the fractal
plt.imshow(bitmap, extent=(xmin, xmax, ymin, ymax), cmap='hot')
plt.colorbar()
plt.title("Mandelbrot Fractal")
plt.show()
