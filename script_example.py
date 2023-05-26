# %%
import matplotlib.pyplot as plt

from clampsuite import ExpManager

# This how to use the experiment manager ExpManager to analyze data.
# To load files just provide the analysis type and a file path in str, PurePath, or Path
# format or a list or tuple of file paths.
# %%
exp_manager = ExpManager()

# %%
# Create a list of acquisitions to open or just a single file.
# The experiment manager can deal with missing files such if you specify 1-10 and 8
# is missing.
file_paths = [f"<insert path and with file prefix>{i}.mat" for i in range(1, 11)]
exp_manager.create_exp(analysis="mini", file=file_paths)

# %%
# Analyze mini acquistions using default settings.
# To specify settings just add the need keyword arguments.
exp_manager.analyze_exp("mini")

# %%
exp_manager.run_final_analysis()

# %%
# Save individual parts of the data.zs
exp_manager.save_acqs("<insert path to folder>")
exp_manager.save_final_analysis("<insert path to folder>")
exp_manager.save_ui_prefs("<insert path to folder>")

# %%
# Save all data at once
exp_manager.save_data("<insert path to folder>")

# %%
# Load existing data, note that a yaml file needs to be include.
file_path = "<insert path to folder>"
exp_manager.load_final_analysis("mini", file_path)


# %%
# Load a single acquisition
acq = ExpManager.load_acq(
    analysis="mini",
    path=r"<insert path to file>",
)

# %%
plt.plot(acq.plot_acq_x(), acq.plot_acq_y())
