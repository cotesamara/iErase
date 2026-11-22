import argparse
from pathlib import Path
from time import perf_counter

from gif_processing import process_gif


# This is our one AI test file.
# It can test any GIF and any rembg model from the terminal.
parser = argparse.ArgumentParser(description="Test AI background removal on a GIF")
parser.add_argument(
    "--input",
    default="assets/cat.gif",
    help="GIF we want to test",
)
parser.add_argument(
    "--model",
    default="u2net",
    help="rembg model name, like u2netp or u2net",
)
parser.add_argument(
    "--output",
    help="Where finished GIF should save",
)
args = parser.parse_args()

# Make a good output name automatically if user did not give one.
input_path = Path(args.input)
output_path = args.output or f"outputs/ai_testing/{input_path.stem}_{args.model}.gif"

start_time = perf_counter()

process_gif(
    input_path=input_path,
    output_path=output_path,
    method="ai",
    model=args.model,
)

seconds = perf_counter() - start_time
print(f"AI model {args.model} took {seconds:.1f} seconds")
