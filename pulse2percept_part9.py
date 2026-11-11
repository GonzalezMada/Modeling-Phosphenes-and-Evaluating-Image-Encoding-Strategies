
"""
Bridge MATLAB R2019a <-> Python 3.11
Comparison of pulse2percept ScoreboardModel and AxonMapModel.

Communication through MAT-files:
    MATLAB -> input .mat -> Python
    Python -> output .mat -> MATLAB
"""

import sys
import numpy as np
import scipy.io as sio
import pulse2percept as p2p

from pulse2percept.implants import DiskElectrode, ElectrodeArray
from pulse2percept.implants.retina import RetinalImplant
from pulse2percept.models.retina import ScoreboardModel, AxonMapModel
from pulse2percept.topography.retina import RetinalMap

import pulse2percept.models.retina.beyeler2019 as p2p_beyeler2019

_original_fast_scoreboard = p2p_beyeler2019.fast_scoreboard


def fast_scoreboard_float32(
    stim_values,
    x_el,
    y_el,
    x_grid,
    y_grid,
    *args
):
    """
    Convert numerical arrays to contiguous float32 before
    calling the compiled Cython Scoreboard kernel.
    """

    stim_values = np.ascontiguousarray(
        stim_values, dtype=np.float32
    )

    x_el = np.ascontiguousarray(
        x_el, dtype=np.float32
    )

    y_el = np.ascontiguousarray(
        y_el, dtype=np.float32
    )

    x_grid = np.ascontiguousarray(
        x_grid, dtype=np.float32
    )

    y_grid = np.ascontiguousarray(
        y_grid, dtype=np.float32
    )

    return _original_fast_scoreboard(
        stim_values,
        x_el,
        y_el,
        x_grid,
        y_grid,
        *args
    )


# Replace the original function used by ScoreboardModel
p2p_beyeler2019.fast_scoreboard = fast_scoreboard_float32

print("Scoreboard float32 compatibility patch installed.")

class LinearMagnificationMap(RetinalMap):
    """Linear retinal map matching MATLAB's umPerDeg conversion."""

    def __init__(self, um_per_deg):
        super().__init__()
        self.um_per_deg = float(um_per_deg)

    def dva_to_ret(self, xdva, ydva):
        return (
            np.asarray(xdva, dtype=np.float64) * self.um_per_deg,
            np.asarray(ydva, dtype=np.float64) * self.um_per_deg
        )

    def ret_to_dva(self, xret, yret):
        return (
            np.asarray(xret, dtype=np.float64) / self.um_per_deg,
            np.asarray(yret, dtype=np.float64) / self.um_per_deg
        )


def unpack_percept(percept):
    """Return a 2-D frame and 1-D x/y axes."""

    data = np.asarray(percept.data, dtype=np.float64)

    if data.ndim == 3:
        data = data[:, :, 0]
    elif data.ndim != 2:
        raise ValueError(
            f"Unexpected Percept data dimensions: {data.shape}"
        )

    xcoord = np.asarray(percept.xdva, dtype=np.float64)
    ycoord = np.asarray(percept.ydva, dtype=np.float64)

    if xcoord.ndim == 2:
        xcoord = xcoord[0, :]
    else:
        xcoord = xcoord.reshape(-1)

    if ycoord.ndim == 2:
        ycoord = ycoord[:, 0]
    else:
        ycoord = ycoord.reshape(-1)

    if data.shape != (ycoord.size, xcoord.size):
        if data.T.shape == (ycoord.size, xcoord.size):
            data = data.T
        else:
            raise ValueError(
                "Percept data and coordinate axes have inconsistent sizes: "
                f"data={data.shape}, x={xcoord.size}, y={ycoord.size}"
            )

    return data, xcoord, ycoord


def scalar(mat, name):
    """Extract one scalar from a MATLAB MAT-file."""
    return np.asarray(mat[name]).squeeze().item()


def matlab_string(mat, name):
    """Convert a MATLAB character array into a Python string."""
    value = np.asarray(mat[name]).squeeze()

    if value.ndim == 0:
        return str(value.item())

    return "".join(str(v) for v in value.reshape(-1)).strip()


def run_comparison(input_file, output_file):

    print("Loading MATLAB input parameters...")

    mat = sio.loadmat(input_file)

    # ------------------------------------------------------------
    # 1. Read parameters from MATLAB
    # ------------------------------------------------------------

    x_elec_um = np.asarray(
        mat["x_elec_um"], dtype=np.float32
    ).ravel()

    y_elec_um = np.asarray(
        mat["y_elec_um"], dtype=np.float32
    ).ravel()

    currents_uA = np.asarray(
        mat["currents_uA"], dtype=np.float32
    ).ravel()

    active_electrodes = np.asarray(
        mat["active_electrodes"], dtype=bool
    ).ravel()

    electrode_radius_um = float(
        scalar(mat, "electrode_radius_um")
    )

    rho_um = float(scalar(mat, "rho_um"))
    lambda_um = float(scalar(mat, "lambda_um"))
    um_per_deg = float(scalar(mat, "um_per_deg"))
    max_ecc = float(scalar(mat, "max_ecc"))
    map_res = float(scalar(mat, "map_res"))

    od_x = float(scalar(mat, "od_x"))
    od_y = float(scalar(mat, "od_y"))

    n_axons = int(scalar(mat, "n_axons"))

    ax_segments_range = np.asarray(
        mat["ax_segments_range"], dtype=np.float64
    ).reshape(-1)

    n_ax_segments = int(scalar(mat, "n_ax_segments"))

    min_ax_sensitivity = float(
        scalar(mat, "min_ax_sensitivity")
    )

    meridian_blend = float(
        scalar(mat, "meridian_blend")
    )

    axon_pickle_file = matlab_string(
        mat, "axon_pickle_file"
    )

    # ------------------------------------------------------------
    # 2. Validate electrode data
    # ------------------------------------------------------------

    n_electrodes = x_elec_um.size

    if not (
        y_elec_um.size
        == currents_uA.size
        == active_electrodes.size
        == n_electrodes
    ):
        raise ValueError(
            "Electrode coordinates, currents and active mask "
            "must have equal lengths."
        )

    if n_electrodes == 0:
        raise ValueError("No electrodes were supplied by MATLAB.")

    if not np.any(active_electrodes & (currents_uA > 0)):
        raise ValueError(
            "No active electrode has a positive stimulation current."
        )

    if electrode_radius_um <= 0:
        raise ValueError("Electrode radius must be positive.")

    # ------------------------------------------------------------
    # 3. Construct the custom electrode array and stimulus
    # ------------------------------------------------------------

    electrode_dict = {}
    stimulus = {}

    for idx in range(n_electrodes):

        name = f"E{idx + 1:04d}"

        is_active = bool(active_electrodes[idx])

        # Create every electrode, including inactive electrodes.
        electrode_dict[name] = DiskElectrode(
            float(x_elec_um[idx]),
            float(y_elec_um[idx]),
            0.0,
            electrode_radius_um,
            name=name,
            activated=is_active
        )

        # Only active electrodes receive stimulation.
        if is_active and currents_uA[idx] > 0:
            stimulus[name] = float(currents_uA[idx])

    if not stimulus:
        raise ValueError("The stimulus dictionary is empty.")

    print("Number of electrodes:", n_electrodes)
    print("Number of stimulated electrodes:", len(stimulus))

    implant = RetinalImplant(
        ElectrodeArray(electrode_dict),
        eye="right"
    )

    # ------------------------------------------------------------
    # 4. Retinal map and common model parameters
    # ------------------------------------------------------------

    retinal_map = LinearMagnificationMap(um_per_deg)

    common_model_params = dict(
        xrange=(-max_ecc, max_ecc),
        yrange=(-max_ecc, max_ecc),
        step=1.0 / map_res,
        visual_field_map=retinal_map,
        implant_position=(0, 0),
        implant_rotation=0,
        n_gray=None,
        thresh_percept=0,
        verbose=False
    )

    # ------------------------------------------------------------
    # 5. pulse2percept ScoreboardModel
    # ------------------------------------------------------------

    print("\nBuilding pulse2percept ScoreboardModel...")

    p2p_score_model = ScoreboardModel(
        implant,
        rho=rho_um,
        **common_model_params
    )

    p2p_score_model.build()

    print("Running Scoreboard prediction...")

    p2p_score_percept = p2p_score_model.predict_percept(
        stimulus
    )

    p2p_score_data, p2p_x, p2p_y = unpack_percept(
        p2p_score_percept
    )

    print("Scoreboard prediction completed.")
    print("Scoreboard data shape:", p2p_score_data.shape)

    # ------------------------------------------------------------
    # 6. pulse2percept AxonMapModel
    # ------------------------------------------------------------

    print("\nBuilding pulse2percept AxonMapModel...")

    p2p_axon_model = AxonMapModel(
        implant,
        rho=rho_um,
        lam=lambda_um,
        loc_od=(od_x, od_y),
        n_axons=n_axons,
        axons_range=(-180, 180),
        n_ax_segments=n_ax_segments,
        ax_segments_range=tuple(ax_segments_range),
        min_ax_sensitivity=min_ax_sensitivity,
        meridian_blend=meridian_blend,
        axon_pickle=axon_pickle_file,
        ignore_pickle=False,
        **common_model_params
    )

    p2p_axon_model.build()

    print("Running AxonMap prediction...")

    p2p_axon_percept = p2p_axon_model.predict_percept(
        stimulus
    )

    p2p_axon_data, p2p_axon_x, p2p_axon_y = unpack_percept(
        p2p_axon_percept
    )

    print("AxonMap prediction completed.")
    print("AxonMap data shape:", p2p_axon_data.shape)

    # ------------------------------------------------------------
    # 7. Verify common visual-field grid
    # ------------------------------------------------------------

    if not (
        np.allclose(p2p_x, p2p_axon_x)
        and np.allclose(p2p_y, p2p_axon_y)
    ):
        raise ValueError(
            "pulse2percept Scoreboard and AxonMap grids "
            "are not identical."
        )

    # ------------------------------------------------------------
    # 8. Save results for MATLAB
    # ------------------------------------------------------------

    print("\nSaving pulse2percept results...")

    output = {
        "p2p_score_data": p2p_score_data,
        "p2p_axon_data": p2p_axon_data,
        "p2p_x": p2p_x.reshape(1, -1),
        "p2p_y": p2p_y.reshape(-1, 1),
        "p2p_version": str(
            getattr(p2p, "__version__", "unknown")
        )
    }

    sio.savemat(
        output_file,
        output,
        do_compression=True
    )

    print("\nComparison completed successfully.")
    print("pulse2percept version:", output["p2p_version"])
    print("Output file:", output_file)


if __name__ == "__main__":

    if len(sys.argv) != 3:
        raise ValueError(
            "Usage: python pulse2percept_part9.py "
            "input.mat output.mat"
        )

    run_comparison(sys.argv[1], sys.argv[2])
