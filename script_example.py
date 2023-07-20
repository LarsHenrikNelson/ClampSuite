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
file_paths = [f"my/path/to_file/AD_{i}.mat" for i in range(1, 11)]
exp_manager.create_exp(analysis="mini", file=file_paths)

# %%
# Analyze mini acquistions using default settings.
# To specify settings just add the need keyword arguments.
exp_manager.analyze_exp("mini")

# %%
exp_manager.run_final_analysis()

# %%
# Save individual parts of the data.zs
exp_manager.save_acqs("my/path/to_folder")
exp_manager.save_final_analysis("my/path/to_folder")
exp_manager.save_ui_prefs("my/path/to_folder")

# %%
# Save all data at once
exp_manager.save_data("my/path/to_folder")

# %%
# Load existing "mini" data, note that a yaml file needs to be include.
file_path = "my/path/to_folder"
exp_manager.load_final_analysis("mini", file_path)


# %%
# Load a single acquisition
acq = ExpManager.load_acq(
    analysis="mini",
    path=r"my/path/to_folder/AD_0.mat",
)

# %%
plt.plot(acq.plot_acq_x(), acq.plot_acq_y())
