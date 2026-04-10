<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Optics & Image Analysis Toolkit</title>

<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

<style>
body {
    font-family: "Segoe UI", Tahoma, sans-serif;
    margin: 0;
    background: #f4f6f8;
}

nav {
    background: #1f2937;
    padding: 12px;
    text-align: center;
}

nav button {
    margin: 5px;
    padding: 10px 18px;
    border: none;
    background: #374151;
    color: white;
    border-radius: 6px;
    cursor: pointer;
}

nav button:hover { background: #4b5563; }

.container {
    max-width: 900px;
    margin: auto;
    padding: 30px;
}

.card {
    background: white;
    padding: 25px;
    border-radius: 10px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    margin-bottom: 25px;
}

.tab { display: none; }
.active { display: block; }

input {
    margin: 5px;
    padding: 8px;
    border-radius: 5px;
    border: 1px solid #ccc;
}

button.calc {
    margin-top: 10px;
    padding: 10px 15px;
    background: #2563eb;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

.result {
    margin-top: 15px;
    font-weight: bold;
}

img.preview {
    max-width: 300px;
    margin-top: 15px;
    border-radius: 8px;
}

.logo-container {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 20px;
}

.logo-container img {
    height: 80px;
}
</style>
</head>

<body>

<nav>
    <button onclick="showTab('home')">Home</button>
    <button onclick="showTab('strehl')">Strehl / Encircled Energy</button>
    <button onclick="showTab('rayleigh')">Rayleigh Range</button>
    <button onclick="showTab('gaussian')">Gaussian Beam</button>
</nav>

<div class="container">

<!-- HOME -->
<div id="home" class="tab active">
    <div class="card">
        <h1>Optics & Image Analysis Toolkit</h1>

        <div class="logo-container">
            <img src="zeus_logo.png">
            <img src="nsf_logo.png">
        </div>

        <p>
        This toolkit provides browser-based diagnostics for laser beam analysis.
        Contributions are welcome.
        </p>

        <p>
        Developer: 
        <a href="https://sites.google.com/view/jeremy-rebenstock/about" target="_blank">
        Jeremy Rebenstock
        </a>
        </p>
    </div>
</div>

<!-- STREHL -->
<div id="strehl" class="tab">
    <div class="card">
        <h2>Encircled Energy & Strehl Estimate</h2>

        \[
        E(r) = \int_0^r I(r') 2\pi r' dr'
        \]

        \[
        S \approx \left(\frac{r_{\mathrm{DL}}}{r_{\mathrm{meas}}}\right)^2
        \]

        <input type="file" id="upload"><br>

        <input id="um_per_pixel" placeholder="µm per pixel">
        <input id="r_dl" placeholder="Diffraction-limited radius (µm)"><br>

        <img id="preview" class="preview">
        <canvas id="canvas" style="display:none;"></canvas>

        <div id="result" class="result"></div>

        <p style="font-size:0.9em;">
        Reference: Siegman, <i>Lasers</i> (1986)
        </p>
    </div>
</div>

<!-- RAYLEIGH -->
<div id="rayleigh" class="tab">
    <div class="card">
        <h2>Rayleigh Range</h2>

        \[
        w_0 \approx \frac{\lambda f/\#}{\pi}
        \quad
        z_R = \frac{\pi w_0^2}{\lambda}
        \]

        <input id="fnum" placeholder="f-number">
        <input id="lambda" placeholder="Wavelength (m)"><br>

        <button class="calc" onclick="calcRayleigh()">Calculate</button>
        <div id="rayleighResult" class="result"></div>
    </div>
</div>

<!-- GAUSSIAN -->
<div id="gaussian" class="tab">
    <div class="card">
        <h2>Gaussian Beam Propagation</h2>

        \[
        w(z) = w_0 \sqrt{1 + \left(\frac{z}{z_R}\right)^2}
        \]

        <input id="w0_g" placeholder="w0 (m)">
        <input id="lambda_g" placeholder="λ (m)">
        <input id="z_g" placeholder="z (m)"><br>

        <button class="calc" onclick="calcGaussian()">Calculate</button>
        <div id="gaussianResult" class="result"></div>
    </div>
</div>

</div>

<script>
// TAB SWITCH
function showTab(tabId) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
}

// IMAGE PROCESSING + STREHL
document.getElementById('upload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const img = document.getElementById('preview');
    const reader = new FileReader();

    reader.onload = ev => img.src = ev.target.result;
    reader.readAsDataURL(file);

    img.onload = function() {
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);

        const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;

        const width = canvas.width;
        const height = canvas.height;

        let intensity = new Array(width * height);
        let total = 0;

        for (let i = 0; i < data.length; i += 4) {
            let idx = i/4;
            let I = 0.299*data[i] + 0.587*data[i+1] + 0.114*data[i+2];
            intensity[idx] = I;
            total += I;
        }

        // centroid
        let xSum=0, ySum=0;
        for (let y=0; y<height; y++) {
            for (let x=0; x<width; x++) {
                let I = intensity[y*width + x];
                xSum += x*I;
                ySum += y*I;
            }
        }

        let x0 = xSum/total;
        let y0 = ySum/total;

        let radial = [];

        for (let y=0; y<height; y++) {
            for (let x=0; x<width; x++) {
                let I = intensity[y*width + x];
                let r = Math.sqrt((x-x0)**2 + (y-y0)**2);
                radial.push({r,I});
            }
        }

        radial.sort((a,b)=>a.r-b.r);

        let cumulative=0;
        let target = 0.8*total;
        let r_pix=0;

        for (let i=0; i<radial.length; i++) {
            cumulative += radial[i].I;
            if (cumulative >= target) {
                r_pix = radial[i].r;
                break;
            }
        }

        let um_per_pixel = parseFloat(document.getElementById('um_per_pixel').value);
        let r_dl = parseFloat(document.getElementById('r_dl').value);

        let r_um = r_pix * um_per_pixel;

        let strehl = (r_dl / r_um)**2;

        document.getElementById('result').innerText =
            `r₈₀ = ${r_pix.toFixed(2)} px (${r_um.toFixed(2)} µm)\nStrehl ≈ ${strehl.toFixed(3)}`;
    };
});

// RAYLEIGH
function calcRayleigh() {
    let fnum = parseFloat(document.getElementById('fnum').value);
    let lambda = parseFloat(document.getElementById('lambda').value);

    let w0 = lambda * fnum / Math.PI;
    let zR = Math.PI * w0 * w0 / lambda;

    document.getElementById('rayleighResult').innerText =
        `zR = ${zR.toExponential(3)} m`;
}

// GAUSSIAN
function calcGaussian() {
    let w0 = parseFloat(document.getElementById('w0_g').value);
    let lambda = parseFloat(document.getElementById('lambda_g').value);
    let z = parseFloat(document.getElementById('z_g').value);

    let zR = Math.PI * w0 * w0 / lambda;
    let w = w0 * Math.sqrt(1 + (z/zR)**2);

    document.getElementById('gaussianResult').innerText =
        `w(z) = ${w.toExponential(3)} m`;
}
</script>

</body>
</html>
