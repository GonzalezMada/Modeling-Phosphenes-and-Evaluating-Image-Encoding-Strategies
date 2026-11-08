# Retinal Phosphene Simulator / Simulateur de phosphènes rétiniens

**[English](#english)** | **[Français](#français)**

---

<a id="english"></a>
## English

### Overview

This MATLAB project simulates what a patient with a retinal visual prosthesis could perceive. Starting from an input image and a parametric electrode grid, it computes the stimulation of each electrode and renders the resulting **phosphenes** (small perceived spots of light), first in the frame of the electrode array and then at their true position on the retina.

It is a **baseline simulator**: a simple, parameterizable pipeline meant as a reference before any optimization of the phosphene rendering.

### Features

- Parametric electrode grid (number, spacing and diameter in µm; square or hexagonal layout), drawn to scale.
- Retina reference grid in degrees of visual angle (concentric eccentricity circles, radial lines, fovea and optic disc), without axon fibers.
- Placement of the electrode grid on the retina from its distance to the fovea (µm) and its tilt (degrees), with 288 µm = 1° of visual angle.
- Image-to-phosphene pipeline: mean intensity under each electrode, quantization, stimulation current, brightness model, Gaussian phosphenes.
- Display of the phosphenes in the retina frame: black everywhere except at the phosphenes, with no reference grid drawn.

### Requirements

- MATLAB **R2017b or later** (local functions at the end of a script, `isfile`, string arrays).
- No additional toolbox: only base MATLAB functions are used.
- Optional: a grayscale or RGB image. If none is given (or the file is not found), a synthetic test image is used.

### Quick start

1. Put `main_retina_electrodes_phosphenes.m` in a folder and open it in MATLAB.
2. Edit the parameters (see below). The electrode grid parameters are declared **once**, at the top of the file.
3. Set `imgFile` to the path of your image (or `''` to use the synthetic test image).
4. Run the script. Four figures are produced (see "Figures").

To use it as a Live Script: *Live Editor > Save As > MATLAB Live Code File (\*.mlx)*. The functions must stay at the **end** of the file.

### How it works

The script has five parts. Part 4 is the core of the model:

```
image ──► mapped on the grid's field of view
      ──► mean intensity at each electrode (box filter = electrode spacing)
      ──► quantization (nLevels gray levels)
      ──► current   C  = level * Cmax                    (0 to Cmax µA)
      ──► brightness B = a * C^b ,  Bn = B / (a*Cmax^b)  (normalized to [0, 1])
      ──► Gaussian phosphene at each electrode, sigma = sigmaFactor * D
      ──► display (Part 4) and placement on the retina (Part 5)
```

| Part | Content |
|------|---------|
| 1 | Electrode grid drawn to scale (µm) |
| 2 | Retina reference grid (degrees) |
| 3 | Electrode grid placed on the retina grid (offset from the fovea + tilt) |
| 4 | Image to phosphenes, shown next to the input image |
| 5 | Phosphenes placed in the retina frame, black background, no reference grid |

**Step details (Part 4)**

1. **Grid in degrees.** Electrode positions (µm) are converted to degrees with `umPerDeg = 288`. The field of view covered by the grid is the distance between the outer electrode centers plus one pitch.
2. **Image mapping.** The image is optionally center-cropped to the grid's aspect ratio, then stretched over the grid's field of view: `pixels per degree = image size in pixels / field of view in degrees`.
3. **Electrode intensity.** Each electrode is placed on the nearest pixel. Its intensity is the mean of the image over a box whose size is the electrode spacing converted to pixels, rounded to the nearest odd integer (so the window is centered on a pixel). The mean is computed by convolution with `K = ones(nh, nw) / (nh*nw)`; pixels outside the image count as 0.
4. **Quantization.** `Iq = round(I * (nLevels-1)) / (nLevels-1)`.
5. **Current.** `C = Iq * Cmax`, from 0 to `Cmax` µA.
6. **Brightness.** Power law `B = a * C^b`, normalized by its value at `Cmax` so that the brightest level is 1. Level 0 gives no phosphene.
7. **Phosphene.** A 2-D Gaussian centered on each electrode with `sigma = sigmaFactor * D` (D = electrode diameter in degrees) and peak value `Bn`. Overlapping phosphenes add up and the result is clipped to 1.

### Parameters

All values below are the defaults of the current script.

**Electrode grid (declared once at the top)**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nRows`, `nCols` | 32, 32 | Number of electrodes (rows, columns) |
| `pitchX`, `pitchY` | 250, 250 | Center-to-center spacing [µm] |
| `elecDiam` | 100 | Electrode diameter [µm] |
| `layout` | `"square"` | `"square"` or `"hexagonal"` (odd rows shifted by half a pitch) |
| `umPerDeg` | 288 | Retinal magnification: 1° = 288 µm |
| `centerGrid` (Part 1) | `true` | Center the grid on the origin; parts 3 and 4 always center it |

**Retina grid (Parts 2 and 3)**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `maxEcc` | 30 | Outermost eccentricity circle [°]; also the half-width of the Part 5 display |
| `eccStep` | 10 | Spacing between circles [°] |
| `angStep` | 45 | Angle between radial lines [°] |
| `odCenter` | `[16.8, 1.9]` | Optic disc center relative to the fovea [°] |
| `odSize` | `[6.5, 6.5]` (Part 2), `[5.5, 6.5]` (Part 3) | Optic disc width and height [°] |
| `foveaRadius` | 2.5 | Radius of the fovea marker [°] |

**Placement on the retina (Part 3)**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `centerOffset` | `[-650, -700]` | Array center relative to the fovea [x y] in µm (X right, Y up) |
| `tiltDeg` | 10 | Rotation of the array around its center [°], counter-clockwise positive |

**Image to phosphenes (Parts 4 and 5)**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `imgFile` | path to a `.jpg` | Input image; `''` or a missing file gives a synthetic test image |
| `cropToGridAspect` | `true` | Center-crop the image to the grid's aspect ratio (avoids deformation) |
| `nLevels` | 10 | Number of gray levels (e.g. 2, 4, 8 or 10) |
| `Cmax` | 120 | Current of the brightest level [µA] |
| `a`, `b` | 1.24, 1.02 | Brightness model `B = a * C^b` |
| `sigmaFactor` | 0.42 | `sigma = sigmaFactor * D` |
| `canvasPxPerDeg` | 60 | Resolution of the Part 4 phosphene image [pixel/°] |
| `retinaPxPerDeg` | 30 | Resolution of the Part 5 retina image [pixel/°] |
| `showAxes` | `false` | Show X/Y axes in degrees in Part 5 (still no retina grid) |

### Conventions

- **Units:** lengths on the array in µm, positions on the retina in degrees of visual angle.
- **Electrode numbering:** row by row, left to right then top to bottom. Electrode #1 is at the top-left of the array.
- **Axes:** `create_electrode_grid` returns the *image* convention (Y pointing down). `place_grid_on_retina` flips Y so that all retina-frame data has X to the right and Y up.
- **Retina frame:** the fovea is the origin (0, 0).

### Functions

All functions are defined at the end of the script.

| Function | Role |
|----------|------|
| `create_electrode_grid` | Electrode centers (µm) from the grid parameters; returns `x`, `y` and a `coords` table |
| `place_grid_on_retina` | Flips Y, rotates by `tiltDeg`, translates by `centerOffset`, converts µm to degrees |
| `draw_retina_grid` | Draws the polar retina reference grid, optic disc and fovea |
| `sample_image_on_grid` | Maps the image on the grid and returns the mean intensity at each electrode |
| `render_phosphenes` | Sums one Gaussian per electrode on a black canvas |

### Figures

1. **Electrode grid**: the array drawn to scale in µm.
2. **Retina reference grid**: polar grid with optic disc and fovea.
3. **Electrode grid on the retina**: the array at its position and tilt.
4. **Phosphene simulation**: input image (left) and phosphenes in the grid's own frame (right).
5. **Phosphenes on the retina**: phosphenes at their retinal position, black background.

The console also prints the field of view, image resolution, box filter size, Gaussian sigma, brightness at `Cmax` and the first rows of the results table.

### Assumptions and limitations

- The brightness model `B = a * C^b` is a power law in the spirit of Greenwald et al. (2009). The values `a = 1.24` and `b = 1.02` are the project's choices; `b = 1.02` is inside the range reported for one of the two subjects of that study. They are not patient-specific fits.
- Phosphenes are round Gaussians of fixed size. The dependence of phosphene size on current, which varies between patients, and axon-induced elongated phosphenes are **not** modeled.
- The magnification is constant (288 µm/°) over the whole retina.
- The mean intensity uses a box filter whose width equals the electrode spacing (as in Thompson et al., 2003); pixels beyond the image border count as 0, which slightly darkens the outermost electrodes.
- The simulator has not been validated against clinical data.

### Troubleshooting

- *"File not found"*: check `imgFile`; the synthetic test image is used otherwise.
- *Warning about overlapping electrodes*: `elecDiam` is larger than the smallest pitch.
- *Warning about electrodes or phosphenes outside the retina*: reduce `centerOffset`, the grid size, or increase `maxEcc`.
- *Part 5 is slow or uses a lot of memory*: lower `retinaPxPerDeg`.
- *Error about local functions*: the functions must remain at the end of the file, after all script code.

### References

- Greenwald S. H. et al. (2009). *Brightness as a function of current amplitude in human retinal electrical stimulation.*
- Thompson R. W. et al. (2003). *Facial recognition using simulated prosthetic pixelized vision.*
- Dagnelie G. et al. (2006). *Paragraph text reading using a pixelized prosthetic vision simulator.*

---

<a id="français"></a>
## Français

### Présentation

Ce projet MATLAB simule ce que pourrait percevoir un patient porteur d'une prothèse visuelle rétinienne. À partir d'une image d'entrée et d'une grille d'électrodes paramétrable, il calcule la stimulation de chaque électrode et affiche les **phosphènes** obtenus (petites taches lumineuses perçues), d'abord dans le repère de la grille d'électrodes, puis à leur position réelle sur la rétine.

C'est un **simulateur de référence** : un pipeline simple et paramétrable, destiné à servir de base avant toute optimisation du rendu des phosphènes.

### Fonctionnalités

- Grille d'électrodes paramétrable (nombre, espacement et diamètre en µm ; disposition carrée ou hexagonale), affichée à l'échelle.
- Grille de repère de la rétine en degrés d'angle visuel (cercles d'excentricité, lignes radiales, fovéa et disque optique), sans les fibres axonales.
- Placement de la grille d'électrodes sur la rétine à partir de sa distance à la fovéa (µm) et de son inclinaison (degrés), avec 288 µm = 1° d'angle visuel.
- Pipeline image vers phosphènes : intensité moyenne sous chaque électrode, quantification, courant de stimulation, modèle de brillance, phosphènes gaussiens.
- Affichage des phosphènes dans le repère de la rétine : fond noir partout sauf aux phosphènes, sans repère rétinien.

### Prérequis

- MATLAB **R2017b ou plus récent** (fonctions locales à la fin d'un script, `isfile`, tableaux de chaînes).
- Aucune toolbox supplémentaire : seules des fonctions de base de MATLAB sont utilisées.
- Facultatif : une image en niveaux de gris ou en couleur. Sans image (ou si le fichier est introuvable), une image de test synthétique est utilisée.

### Démarrage rapide

1. Placez `main_retina_electrodes_phosphenes.m` dans un dossier et ouvrez-le dans MATLAB.
2. Modifiez les paramètres (voir ci-dessous). Les paramètres de la grille d'électrodes sont déclarés **une seule fois**, en haut du fichier.
3. Renseignez `imgFile` avec le chemin de votre image (ou `''` pour l'image de test synthétique).
4. Lancez le script. Cinq figures sont produites (voir « Figures »).

Pour l'utiliser comme Live Script : *Live Editor > Save As > MATLAB Live Code File (\*.mlx)*. Les fonctions doivent rester à la **fin** du fichier.

### Fonctionnement

Le script comporte cinq parties. La partie 4 est le cœur du modèle :

```
image ──► projetée sur le champ de vision de la grille
      ──► intensité moyenne sur chaque électrode (filtre moyen = espacement)
      ──► quantification (nLevels niveaux de gris)
      ──► courant    C  = niveau * Cmax                   (0 à Cmax µA)
      ──► brillance  B  = a * C^b ,  Bn = B / (a*Cmax^b)  (normalisée dans [0, 1])
      ──► phosphène gaussien sur chaque électrode, sigma = sigmaFactor * D
      ──► affichage (partie 4) et placement sur la rétine (partie 5)
```

| Partie | Contenu |
|--------|---------|
| 1 | Grille d'électrodes affichée à l'échelle (µm) |
| 2 | Grille de repère de la rétine (degrés) |
| 3 | Grille d'électrodes placée sur la rétine (décalage par rapport à la fovéa + inclinaison) |
| 4 | Image vers phosphènes, affichée à côté de l'image d'entrée |
| 5 | Phosphènes placés dans le repère de la rétine, fond noir, sans repère |

**Détail des étapes (partie 4)**

1. **Grille en degrés.** Les positions des électrodes (µm) sont converties en degrés avec `umPerDeg = 288`. Le champ de vision couvert par la grille est la distance entre les centres des électrodes extrêmes, plus un pas.
2. **Projection de l'image.** L'image est éventuellement rognée au centre au rapport largeur/hauteur de la grille, puis étirée sur le champ de vision de la grille : `pixels par degré = taille de l'image en pixels / champ de vision en degrés`.
3. **Intensité d'une électrode.** Chaque électrode est placée sur le pixel le plus proche. Son intensité est la moyenne de l'image sur une fenêtre dont la taille est l'espacement entre électrodes converti en pixels, arrondi à l'entier impair le plus proche (la fenêtre est ainsi centrée sur un pixel). La moyenne est calculée par convolution avec `K = ones(nh, nw) / (nh*nw)` ; les pixels hors de l'image comptent pour 0.
4. **Quantification.** `Iq = round(I * (nLevels-1)) / (nLevels-1)`.
5. **Courant.** `C = Iq * Cmax`, de 0 à `Cmax` µA.
6. **Brillance.** Loi de puissance `B = a * C^b`, normalisée par sa valeur à `Cmax` pour que le niveau le plus clair vaille 1. Le niveau 0 ne donne aucun phosphène.
7. **Phosphène.** Une gaussienne 2D centrée sur chaque électrode, avec `sigma = sigmaFactor * D` (D = diamètre de l'électrode en degrés) et pour amplitude `Bn`. Les phosphènes qui se chevauchent s'additionnent, puis le résultat est limité à 1.

### Paramètres

Les valeurs ci-dessous sont celles par défaut du script actuel.

**Grille d'électrodes (déclarée une seule fois en haut)**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `nRows`, `nCols` | 32, 32 | Nombre d'électrodes (lignes, colonnes) |
| `pitchX`, `pitchY` | 250, 250 | Espacement centre à centre [µm] |
| `elecDiam` | 100 | Diamètre d'une électrode [µm] |
| `layout` | `"square"` | `"square"` ou `"hexagonal"` (lignes impaires décalées d'un demi-pas) |
| `umPerDeg` | 288 | Grossissement rétinien : 1° = 288 µm |
| `centerGrid` (partie 1) | `true` | Centrer la grille sur l'origine ; les parties 3 et 4 la centrent toujours |

**Grille de la rétine (parties 2 et 3)**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `maxEcc` | 30 | Cercle d'excentricité le plus externe [°] ; demi-largeur de l'affichage de la partie 5 |
| `eccStep` | 10 | Espacement entre les cercles [°] |
| `angStep` | 45 | Angle entre les lignes radiales [°] |
| `odCenter` | `[16.8, 1.9]` | Centre du disque optique par rapport à la fovéa [°] |
| `odSize` | `[6.5, 6.5]` (partie 2), `[5.5, 6.5]` (partie 3) | Largeur et hauteur du disque optique [°] |
| `foveaRadius` | 2.5 | Rayon du marqueur de la fovéa [°] |

**Placement sur la rétine (partie 3)**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `centerOffset` | `[-650, -700]` | Centre de la grille par rapport à la fovéa [x y] en µm (X à droite, Y vers le haut) |
| `tiltDeg` | 10 | Rotation de la grille autour de son centre [°], positive dans le sens antihoraire |

**Image vers phosphènes (parties 4 et 5)**

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `imgFile` | chemin d'un `.jpg` | Image d'entrée ; `''` ou un fichier introuvable donne une image de test synthétique |
| `cropToGridAspect` | `true` | Rogner l'image au centre au rapport de la grille (évite la déformation) |
| `nLevels` | 10 | Nombre de niveaux de gris (par ex. 2, 4, 8 ou 10) |
| `Cmax` | 120 | Courant du niveau le plus clair [µA] |
| `a`, `b` | 1.24, 1.02 | Modèle de brillance `B = a * C^b` |
| `sigmaFactor` | 0.42 | `sigma = sigmaFactor * D` |
| `canvasPxPerDeg` | 60 | Résolution de l'image de phosphènes de la partie 4 [pixel/°] |
| `retinaPxPerDeg` | 30 | Résolution de l'image rétinienne de la partie 5 [pixel/°] |
| `showAxes` | `false` | Afficher les axes X/Y en degrés dans la partie 5 (toujours sans repère rétinien) |

### Conventions

- **Unités :** longueurs sur la grille en µm, positions sur la rétine en degrés d'angle visuel.
- **Numérotation des électrodes :** ligne par ligne, de gauche à droite puis de haut en bas. L'électrode n°1 est en haut à gauche de la grille.
- **Axes :** `create_electrode_grid` renvoie la convention *image* (Y vers le bas). `place_grid_on_retina` inverse Y, de sorte que toutes les données dans le repère rétinien ont X vers la droite et Y vers le haut.
- **Repère rétinien :** la fovéa est l'origine (0, 0).

### Fonctions

Toutes les fonctions sont définies à la fin du script.

| Fonction | Rôle |
|----------|------|
| `create_electrode_grid` | Centres des électrodes (µm) à partir des paramètres ; renvoie `x`, `y` et un tableau `coords` |
| `place_grid_on_retina` | Inverse Y, tourne de `tiltDeg`, translate de `centerOffset`, convertit les µm en degrés |
| `draw_retina_grid` | Dessine la grille polaire de la rétine, le disque optique et la fovéa |
| `sample_image_on_grid` | Projette l'image sur la grille et renvoie l'intensité moyenne de chaque électrode |
| `render_phosphenes` | Additionne une gaussienne par électrode sur un fond noir |

### Figures

1. **Grille d'électrodes** : la grille à l'échelle en µm.
2. **Grille de repère de la rétine** : grille polaire avec disque optique et fovéa.
3. **Grille d'électrodes sur la rétine** : la grille à sa position et son inclinaison.
4. **Simulation de phosphènes** : image d'entrée (gauche) et phosphènes dans le repère de la grille (droite).
5. **Phosphènes sur la rétine** : phosphènes à leur position rétinienne, fond noir.

La console affiche aussi le champ de vision, la résolution de l'image, la taille du filtre moyen, le sigma de la gaussienne, la brillance à `Cmax` et les premières lignes du tableau de résultats.

### Hypothèses et limites

- Le modèle de brillance `B = a * C^b` est une loi de puissance dans l'esprit de Greenwald et al. (2009). Les valeurs `a = 1.24` et `b = 1.02` sont des choix du projet ; `b = 1.02` se situe dans la plage rapportée pour l'un des deux sujets de cette étude. Ce ne sont pas des ajustements propres à un patient.
- Les phosphènes sont des gaussiennes rondes de taille fixe. La dépendance de la taille du phosphène au courant, variable selon les patients, et les phosphènes allongés dus aux axones ne sont **pas** modélisés.
- Le grossissement est constant (288 µm/°) sur toute la rétine.
- L'intensité moyenne utilise un filtre dont la largeur est égale à l'espacement entre électrodes (comme chez Thompson et al., 2003) ; les pixels au-delà du bord de l'image comptent pour 0, ce qui assombrit légèrement les électrodes les plus extérieures.
- Le simulateur n'a pas été validé avec des données cliniques.

### Dépannage

- *« File not found »* : vérifiez `imgFile` ; sinon l'image de test synthétique est utilisée.
- *Avertissement de chevauchement des électrodes* : `elecDiam` est plus grand que le plus petit pas.
- *Avertissement d'électrodes ou de phosphènes hors de la rétine* : réduisez `centerOffset` ou la taille de la grille, ou augmentez `maxEcc`.
- *La partie 5 est lente ou consomme beaucoup de mémoire* : diminuez `retinaPxPerDeg`.
- *Erreur liée aux fonctions locales* : les fonctions doivent rester à la fin du fichier, après tout le code du script.

### Références

- Greenwald S. H. et al. (2009). *Brightness as a function of current amplitude in human retinal electrical stimulation.*
- Thompson R. W. et al. (2003). *Facial recognition using simulated prosthetic pixelized vision.*
- Dagnelie G. et al. (2006). *Paragraph text reading using a pixelized prosthetic vision simulator.*
