from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime

##Jeremy Rebenstock 03/03
##jrebenst@umich.edu



def load_image_as_array(path):
    """Load grayscale image as NumPy array of float64."""
    img = Image.open(path).convert("L")
    return np.array(img, dtype=np.float64)

def find_focal_spot_center(img_array):
    """Find center of brightest pixel (approx focal spot center)."""
    y, x = np.unravel_index(np.argmax(img_array), img_array.shape)
    return x, y

def circular_mask(shape, center_x, center_y, radius_px):
    """Boolean circular mask."""
    Y, X = np.ogrid[:shape[0], :shape[1]]
    return (X - center_x)**2 + (Y - center_y)**2 <= radius_px**2


def diffraction_limited_spot_size(wavelength_nm, beam_diameter_inch, focal_length_inch):
    wavelength_um = wavelength_nm / 1000
    beam_diameter_um = beam_diameter_inch * 25_400
    focal_length_um = focal_length_inch * 25_400

    NA = beam_diameter_um / (2 * focal_length_um)
    spot_diameter_um = 1.22 * wavelength_um / NA
    return spot_diameter_um / 2  # radius in µm

def append_strehl_to_csv(
    csv_path,
    image_path,
    strehl_value,
    diffraction_radius_um,
    um_per_pixel
):
    """
    Append a Strehl calculation to a CSV file.
    Creates the file with headers if it does not exist.
    """
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "image_file",
                "strehl_ratio",
                "diffraction_limit_radius_um",
                "um_per_pixel",
                "datetime_run"
            ])

        writer.writerow([
            os.path.basename(image_path),
            f"{strehl_value:.6f}",
            f"{diffraction_radius_um:.4f}",
            f"{um_per_pixel:.4f}",
            datetime.now().isoformat(timespec="seconds")
        ])
        

def strehl_from_image(
    image_path,
    um_per_pixel,
    diffraction_radius_um,
    csv_path="strehl_data.csv",
    plot=True
):
    img = load_image_as_array(image_path)
    cx, cy = find_focal_spot_center(img)

    radius_px = diffraction_radius_um / um_per_pixel

    spot_mask = circular_mask(img.shape, cx, cy, radius_px)
    total_mask = np.ones_like(img, dtype=bool)

    energy_spot = np.sum(img[spot_mask])
    energy_total = np.sum(img[total_mask])

    strehl = energy_spot / energy_total

    # ---- CSV WRITE ----
    append_strehl_to_csv(
        csv_path,
        image_path,
        strehl,
        diffraction_radius_um,
        um_per_pixel
    )

    if plot:
        plt.figure(figsize=(5,5))
        plt.imshow(img, cmap="hot", origin="lower")
        circle = plt.Circle((cx, cy), radius_px, color="cyan", fill=False, lw=2)
        plt.gca().add_patch(circle)
        plt.title(f"Strehl = {strehl:.4f}")
        plt.colorbar(label="Counts")
        plt.show()

    return strehl


####
#### Values to change based on system 

image_path = "20250627Optimized_focal_spot_wObjective_wPM_exptime3e3.tiff"
# Optical parameters ## TA2 
wavelength_nm = 800
beam_diameter_inch = 3.267
focal_length_inch = 8

# Camera calibration
um_per_pixel = 0.085416666667 

# Diffraction limit
spot_radius_um = diffraction_limited_spot_size(
    wavelength_nm,
    beam_diameter_inch,
    focal_length_inch
)
## Can enter diffraction limited spot radius by hand if you want 
## spot_radius_um = 2.7

strehl = strehl_from_image(
    image_path,
    um_per_pixel,
    spot_radius_um,
    plot=False,
    csv_path="strehl_data.csv",
)

## locally: Documents/Research_2/Calculations/Optical_Calculations/strehl_v1.py
print(f"Strehl ratio from = {strehl:.4f}")

## Further improvements/calculations that can be included
## Add parameter for energy: to calculate a0, 
##      Paul suggests calcaulate teh r80: the radius which incircles 80% of the energy
##      Background subtraction feature 