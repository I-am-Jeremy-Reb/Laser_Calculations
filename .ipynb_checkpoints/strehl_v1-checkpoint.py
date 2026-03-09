from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
from datetime import datetime

##Jeremy Rebenstock 03/03/2026
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

def load_background_image(path, target_shape):
    """
    Load background image and verify it matches the focal spot image shape.
    """
    bkg = load_image_as_array(path)

    if bkg.shape != target_shape:
        raise ValueError(
            f"Background image shape {bkg.shape} does not match focal image shape {target_shape}"
        )

    return bkg



import numpy as np
import matplotlib.pyplot as plt

def _encircled_energy_core(img, fraction=0.80):
    """
    Core computation for encircled-energy radius.
    Returns center_x, center_y, radius_px, energy_encircled, total_energy
    """
    center_x, center_y = find_focal_spot_center(img)

    total_energy = np.sum(img)
    if total_energy <= 0:
        raise ValueError("Total energy is zero or negative.")

    Y, X = np.indices(img.shape)
    r = np.sqrt((X - center_x)**2 + (Y - center_y)**2)

    r_flat = r.flatten()
    img_flat = img.flatten()

    sort_idx = np.argsort(r_flat)
    r_sorted = r_flat[sort_idx]
    img_sorted = img_flat[sort_idx]

    cumulative_energy = np.cumsum(img_sorted)

    target_energy = fraction * total_energy
    idx = np.searchsorted(cumulative_energy, target_energy)

    radius_px = r_sorted[idx]
    energy_encircled = cumulative_energy[idx]

    return center_x, center_y, radius_px, energy_encircled, total_energy

def encircled_energy_radius_px(img, fraction=0.80):
    """
    Returns
    -------
    radius_px : float
        Radius containing target energy (pixels)
    """
    _, _, radius_px, _, _ = _encircled_energy_core(img, fraction)
    return radius_px

def encircled_energy_radius_um(img, um_per_pixel, fraction=0.80):
    """
    Returns
    -------
    radius_um : float
        Radius containing target energy (µm)
    """
    _, _, radius_px, _, _ = _encircled_energy_core(img, fraction)
    return radius_px * um_per_pixel

def encircled_energy_value(
    img,
    um_per_pixel,
    fraction=0.80,
    plot=True
):
    """
    Returns
    -------
    energy_encircled : float
        Energy inside the encircled-energy radius
    """
    center_x, center_y, radius_px, energy_encircled, total_energy = \
        _encircled_energy_core(img, fraction)

    radius_um = radius_px * um_per_pixel

    print(f"{fraction*100:}% encircled-energy radius:")
    print(f"  Radius = {radius_px:.2f} pixels")
    print(f"  Radius = {radius_um:.2f} µm")
    print(f"  Energy enclosed = {energy_encircled:.3e}")

    if plot:
        plt.figure(figsize=(5,5))
        plt.imshow(img, cmap="hot", origin="lower", norm="log")
        circle = plt.Circle(
            (center_x, center_y),
            radius_px,
            color="cyan",
            fill=False,
            lw=2
        )
        plt.gca().add_patch(circle)
        plt.title(f"{fraction*100:}% Encircled Energy")
        plt.colorbar(label="Counts")
        plt.show()

    return energy_encircled



def append_strehl_to_csv(
    csv_path,
    image_path,
    strehl_value,
    diffraction_radius_um,
    um_per_pixel,
    r80_um,
    r9995_um,
    background_image_path=None
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
                "EE.8_radius_um",## encircled energy 80%
                "EE.9995_radius_um",## encircled energy 99.95%
                "background image",
                "um_per_pixel",
                "datetime_run",
            ])

        writer.writerow([
            os.path.abspath(image_path),  
            f"{strehl_value:.6f}",
            f"{diffraction_radius_um:.4f}",
            f"{r80_um:.6f}",
            f"{r9995_um:.6f}",
            f"{background_image_path}",
            f"{um_per_pixel:.4f}",
            datetime.now().isoformat(timespec="seconds"),
        ])
        
## Next will update the strehl csv
def strehl_from_image(
    image_path,
    um_per_pixel,
    diffraction_radius_um,
    background_image_path=None,
    plot=True
):
    
    img = load_image_as_array(image_path)
    # Optional background subtraction
    if background_image_path is not None:
        bkg = load_background_image(background_image_path, img.shape)
        img = img - bkg
        img[img < 0] = 0.0  # prevent negative intensities

    cx, cy = find_focal_spot_center(img)
    radius_px = diffraction_radius_um / um_per_pixel ## radius of diffraction limited spot in pixels
    
    ## calculate values based on encircled energies
    r80_px = encircled_energy_radius_px(img =img,fraction = .8)
    r80_um = encircled_energy_radius_um(img = img, um_per_pixel = um_per_pixel,fraction = .8) ##radius of 80% energy included
    r9995_um = encircled_energy_radius_um(img = img, um_per_pixel = um_per_pixel,fraction = .9995) ##radius of 99.95% energy included
    
    E9995    = encircled_energy_value(img = img, um_per_pixel=um_per_pixel, plot=False,fraction = .9995) ## the Energy within the circle of which contains 99.95% of energy
    
    spot_mask = circular_mask(img.shape, cx, cy, radius_px) ## diffraction limited spot 
    ##total_mask = np.ones_like(img, dtype=bool) 
    
    energy_spot = np.sum(img[spot_mask]) ## calculate energy based on radius
    
    print(energy_spot)
    strehl = energy_spot / E9995
    

    # ---- CSV WRITE ---- ## Add other values as desired? 
    csv_path="Focal_Spot_Data/strehl_data.csv"
    append_strehl_to_csv(
        csv_path, ## from current folder
        image_path,
        strehl,
        diffraction_radius_um,
        um_per_pixel,
        r80_um,
        r9995_um,
        background_image_path
    )

    if plot:
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)
        # -------- Left: Linear scale --------
        im0 = axes[0].imshow(img, cmap="hot", origin="lower")
        circle_strehl_0 = plt.Circle((cx, cy),radius_px,color="cyan",linestyle="--",fill=False,lw=2,
            label=f"Diffr. lim. spot (Strehl = {strehl:.4f})"
        )
        circle_80_0 = plt.Circle((cx, cy),r80_px,color="blue", linestyle="-.",fill=False,lw=2,
            label=f"80% encircled energy radius = {np.round(r80_um, 4)} µm"
        )
        axes[0].add_patch(circle_strehl_0)
        axes[0].add_patch(circle_80_0)
        axes[0].set_title(os.path.basename(image_path))
        fig.colorbar(im0, ax=axes[0], label="Counts")
        axes[0].legend()
        
        # -------- Right: Log scale --------
        im1 = axes[1].imshow(img, cmap="hot", origin="lower", norm="log")
        circle_strehl_1 = plt.Circle((cx, cy),radius_px,color="cyan",linestyle="--",fill=False,lw=2,
            label=f"Diffr. lim. spot (Strehl = {strehl:.4f})"
        )
        circle_80_1 = plt.Circle((cx, cy),r80_px,color="blue",linestyle="-.",fill=False,lw=2,
            label=f"80% encircled energy radius = {np.round(r80_um, 4)} µm"
        )
        axes[1].add_patch(circle_strehl_1)
        axes[1].add_patch(circle_80_1)
        axes[1].set_title("Log scale")
        fig.colorbar(im1, ax=axes[1], label="Counts")
        axes[1].legend()
        
        
        plt.show()




    return strehl,r80_um

## change based on system 
##image_path = "Focal_Spot_Images/Focal_Spot_Tests/10mJ_New_Optimized_FocalSpotWithDPM_2025-07-17_1109AM.tiff"
image_path = "Focal_Spot_Images/Focal_Spot_Tests/20250627Optimized_focal_spot_wObjective_wPM_exptime3e3.tiff"

## Optical parameters for Diffraction spot size calculation
## TA2 values 
wavelength_nm = 800
beam_diameter_inch = 3.267
focal_length_inch = 8
##
# Camera calibration
um_per_pixel = 0.085416666667 

# Calculated Diffraction limit spot radius
spot_radius_um = diffraction_limited_spot_size(
    wavelength_nm,
    beam_diameter_inch,
    focal_length_inch
)
#### Can enter diffraction limited spot radius by hand if you want 
## spot_radius_um = 2.7

strehl,r80_um = strehl_from_image(
    image_path,
    um_per_pixel,
    spot_radius_um,
    background_image_path=None,
    plot=True,
)


print(f"Strehl ratio from = {strehl:.4f}")
print(f"80% enclosed enregy radius = {r80_um:.4f}")


## Further improvements/calculations that can be included
## Add parameter for energy: to calculate a0, 
##      Paul suggests calcaulate teh r80: the radius which incircles 80% of the energy
##      Background subtraction feature 