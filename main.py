from PIL import Image
from image_processing_old import remove_background

image = Image.open("assets/sample_input.png")

result = remove_background(image)

result.save("outputs/sample_output.png")

print("Background removed successfully!")