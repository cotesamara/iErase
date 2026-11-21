from PIL import Image
from image_processing_sammy import remove_solid_background, ai_remove_background

gif = Image.open("assets/sample.gif")
gif.seek(2)

no_ai_result = remove_solid_background(gif)
ai_result = ai_remove_background(gif)

no_ai_result.save("outputs/sample_output-_aiSammy.png")
ai_result.save("outputs/sample_output_noaiSammy.png")

print("Background removed successfully!")