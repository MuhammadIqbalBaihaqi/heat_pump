# # T-s diagram of working fluids
# # Contributor: Matahari Arsyabil Muhammad Choiri, Sherryn, Muhammad Jati, Muhammad Zelot Zoha
# from numpy import *
# from matplotlib.pyplot import *
# import math
# import CoolProp
# from CoolProp.CoolProp import PropsSI

# def TSdiagram(Fluid):
#     """
#     Plot the saturation curve of a given fluid in T-s coordinates.

#     Parameters:
#     Fluid (str): Name of the fluid (e.g., 'propane').

#     """
#     # Get critical and triple point temperatures
#     T_crit = PropsSI('Tcrit', Fluid)
#     T_triple = PropsSI('Ttriple', Fluid)

#     # Generate temperature range
#     T = linspace(T_triple, T_crit, 1000)

#     # Initialize lists for entropy values
#     s_1 = []  # Entropy for saturated vapor (Q=1)
#     s_0 = []  # Entropy for saturated liquid (Q=0)

#     # Calculate properties at each temperature in the range
#     for temp in T:
#         s_1.append(PropsSI('S', 'T', temp, 'Q', 1, Fluid))
#         s_0.append(PropsSI('S', 'T', temp, 'Q', 0, Fluid))

#     # Convert entropy from J/(kg⋅K) to kJ/(kg⋅K) for better readability
#     s_0 = [s / 1000 for s in s_0]
#     s_1 = [s / 1000 for s in s_1]

#     # Combined data for a closed-loop plot
#     s_combined = s_0 + s_1[::-1]
#     T_combined = concatenate([T, T[::-1]])

#     # Plot the saturation graph in T-s coordinates
#     figure()
#     plot(s_combined, T_combined, 'k')
#     xlabel('$s$ (kJ/(kg⋅K)', fontsize=12)
#     ylabel('$T$ (K)', fontsize=12)
#     x_min, x_max = min(s_combined), max(s_combined)
#     y_min, y_max = min(T_combined), max(T_combined)

#     x_min = math.floor(x_min)
#     x_max = math.ceil(x_max)

#     y_min = math.floor(y_min/100)*100
#     y_max = math.ceil(y_max/100)*100

#     xlim(x_min, x_max)  # Sedikit memperbesar batas sumbu X
#     ylim(y_min, y_max)  # Sedikit memperbesar batas sumbu Y
#     title(Fluid)
#     grid(False)

#     # Adjust layout to prevent axis labels from being clipped
#     tight_layout()


# from numpy import *
# from matplotlib.pyplot import *
# import math
# import CoolProp
# from CoolProp.CoolProp import PropsSI

# def TSdiagram(Fluid, extracted_ts=None):
#     """
#     Plot the saturation curve of a given fluid in T-s coordinates.

#     Parameters:
#     Fluid (str): Name of the fluid (e.g., 'propane').
#     extracted_ts (array-like): Optional T-s data (array of [T, s] values) to overlay on the diagram.

#     """
#     # Get critical and triple point temperatures
#     T_crit = PropsSI('Tcrit', Fluid)
#     T_triple = PropsSI('Ttriple', Fluid)

#     # Generate temperature range
#     T = linspace(T_triple, T_crit, 1000)

#     # Initialize lists for entropy values
#     s_1 = []  # Entropy for saturated vapor (Q=1)
#     s_0 = []  # Entropy for saturated liquid (Q=0)

#     # Calculate properties at each temperature in the range
#     for temp in T:
#         s_1.append(PropsSI('S', 'T', temp, 'Q', 1, Fluid) / 1000)  # Convert to kJ/kg.K
#         s_0.append(PropsSI('S', 'T', temp, 'Q', 0, Fluid) / 1000)  # Convert to kJ/kg.K

#     # Combined data for a closed-loop plot
#     s_combined = s_0 + s_1[::-1]
#     T_combined = concatenate([T, T[::-1]])

#     # Plot the saturation graph in T-s coordinates
#     figure()
#     plot(s_combined, T_combined, 'k', label='Saturation Curve')

#     # If extracted T-s data is provided, overlay it on the plot
#     if extracted_ts is not None:
#         T_extracted, s_extracted = zip(*extracted_ts)
#         s_extracted = np.array([s for s in s_extracted])  
#         #plot(s_extracted, T_extracted, color='blue', linestyle='solid', linewidth=1, label='Process Cycle')
#         scatter(s_extracted,T_extracted,s=1)

#     xlabel('$s$ (kJ/(kg⋅K))', fontsize=12)
#     ylabel('$T$ (K)', fontsize=12)
#     x_min, x_max = min(s_combined), max(s_combined)
#     y_min, y_max = min(T_combined), max(T_combined)

#     x_min = math.floor(x_min)
#     x_max = math.ceil(x_max)

#     y_min = math.floor(y_min/100)*100
#     y_max = math.ceil(y_max/100)*100

#     xlim(x_min, x_max)  # Sedikit memperbesar batas sumbu X
#     ylim(y_min, y_max)  # Sedikit memperbesar batas sumbu Y
#     title(Fluid)
#     grid(False)
#     legend()

#     # Adjust layout to prevent axis labels from being clipped
#     tight_layout()
import numpy as np
import matplotlib.pyplot as plt
import math
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes, mark_inset
from CoolProp.CoolProp import PropsSI


def add_zoom_inset(ax, x0, y0, dx, dy, zoom=2, loc="upper right",
                   edgecolor="red", linestyle="--", linewidth=1.5,labels=None):
    """
    Add a zoomed inset to a matplotlib Axes.
    """
    axins = zoomed_inset_axes(ax, zoom=zoom, loc=loc)

    # 🔑 Replot all lines that exist in the main axes
    for line in ax.get_lines():
        axins.plot(line.get_xdata(), line.get_ydata(),
                   color=line.get_color(), linestyle=line.get_linestyle(),
                   linewidth=line.get_linewidth(), label=line.get_label())
        
        # 🔑 Copy all scatter points
    for pathcoll in ax.collections:
        offsets = pathcoll.get_offsets()
        axins.scatter(offsets[:, 0], offsets[:, 1],
                      color=pathcoll.get_facecolor()[0],
                      s=pathcoll.get_sizes()[0])
    # 🔑 Copy labels if provided
    if labels is not None:
        s_cycle, T_cycle, name_ideal, name_real = labels
        for x, y, n_i, n_r in zip(s_cycle, T_cycle, name_ideal, name_real):
            axins.text(x-0.0075, y-1.9, n_i, fontsize=7, color="blue", ha="center")
            axins.text(x-0.001, y+0.013, n_r, fontsize=7, color="red", ha="center")

    # Set zoom limits
    axins.set_xlim(x0 - dx, x0 + dx)
    axins.set_ylim(y0 - dy, y0 + dy)
    axins.set_xticks([])
    axins.set_yticks([])

    # Draw zoom box
    mark_inset(ax, axins,
               loc1=1, loc2=1,
               fc="none",
               ec=edgecolor,
               lw=linewidth,
               ls=linestyle)

    return axins



def TSdiagram(fluid, process_cycles=None, ax=None, zoom_insets=None,
              name_ideal=None, name_real=None,figsize=(8,6)):
    """
    Plot the T–s saturation curve for a given fluid and overlay one or more process cycles.
    Optionally add one or multiple zoom insets.
    """
    # Critical & triple point
    T_crit = PropsSI('Tcrit', fluid)
    T_triple = PropsSI('Ttriple', fluid)

    # Temperature range
    T = np.linspace(T_triple, T_crit, 1000)

    # Entropy at saturation
    s_liquid = np.array([PropsSI('S', 'T', temp, 'Q', 0, fluid) / 1000 for temp in T])
    s_vapor = np.array([PropsSI('S', 'T', temp, 'Q', 1, fluid) / 1000 for temp in T])

    # Plot
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    s_curve = np.concatenate([s_liquid, s_vapor[::-1]])
    T_curve = np.concatenate([T, T[::-1]])
    ax.plot(s_curve, T_curve, 'k', label='Saturation Curve', linewidth=1.5)

    # Process cycles
    if process_cycles is not None:
        colors = plt.cm.tab10.colors
        for i, (T_cycle, s_cycle) in enumerate(process_cycles):
            color = colors[i % len(colors)]
            T_cycle = np.asarray(T_cycle)
            s_cycle = np.asarray(s_cycle)
            # Ensure cycle closes
            if (T_cycle[0] != T_cycle[-1]) or (s_cycle[0] != s_cycle[-1]):
                T_cycle = np.append(T_cycle, T_cycle[0])
                s_cycle = np.append(s_cycle, s_cycle[0])
            ax.plot(s_cycle, T_cycle, color=color, linewidth=1, label=f'Process Cycle {i+1}')
            ax.scatter(s_cycle, T_cycle, color=color, s=10)

             # 🔑 Add labels to main plot
            if name_ideal is not None and name_real is not None:
                for x, y, n_i, n_r in zip(s_cycle, T_cycle, name_ideal, name_real):
                    ax.text(x, y, n_i, fontsize=9, color="blue", ha="center")
                    ax.text(x, y, n_r, fontsize=8, color="red", ha="center")

    # Labels & limits
    ax.set_xlabel("Entropy, $s$ (kJ/kg⋅K)", fontsize=12)
    ax.set_ylabel("Temperature, $T$ (K)", fontsize=12)
    ax.set_title(f"T–s Diagram of {fluid}")

    ax.set_xlim(math.floor(s_liquid.min()), math.ceil(s_vapor.max()))
    ax.set_ylim(math.floor(T_triple / 100) * 100, math.ceil(T_crit / 100) * 100)

    ax.grid(True, linestyle="--", linewidth=0.5)
    ax.legend()

    # Handle zoom insets
    if zoom_insets is not None:
        if isinstance(zoom_insets, dict):  # single inset
            add_zoom_inset(ax, labels=(s_cycle, T_cycle, name_ideal, name_real), **zoom_insets)
        elif isinstance(zoom_insets, list):  # multiple insets
            for inset in zoom_insets:
                add_zoom_inset(ax, labels=(s_cycle, T_cycle, name_ideal, name_real), **inset)

    return ax

# T1 = [300, 500, 500, 300, 300]
# s1 = [1.0, 1.0, 6.0, 6.0, 1.0]

# fig, ax = plt.subplots()

# zoom1 = {
#     "x": s1, "y": T1,
#     "x0": 3.5, "y0": 400,
#     "dx": 0.3, "dy": 100,
#     "zoom": 0.5, "loc": "upper left",
#     "edgecolor": "blue", "linestyle": "-.", "linewidth": 2
# }
# zoom2 = {
#     "x": s1, "y": T1,
#     "x0": 1.0, "y0": 300,
#     "dx": 0.5, "dy": 100,
#     "zoom": 0.5, "loc": "lower right",
#     "edgecolor": "green", "linestyle": "--", "linewidth": 1.5
# }

# TSdiagram("Water", process_cycles=[(T1, s1)], ax=ax, zoom_insets=[zoom1, zoom2])
# plt.show()


# T1 = [300, 500, 500, 300, 300]
# s1 = [1.0, 1.0, 6.0, 6.0, 1.0]

# T2 = [320, 520, 520, 320, 320]
# s2 = [1.5, 1.5, 6.5, 6.5, 1.5]

# TSdiagram("Water", process_cycles=[(T1, s1), (T2, s2)])
# plt.show()


# Example usage:
# import numpy as np
# cycle1 = np.array([[300, 1.5], [350, 2.0], [400, 2.5]])  # [T, s]
# cycle2 = np.array([[310, 1.6], [360, 2.1], [410, 2.6]])
# TSdiagram('Water', process_cycles=[cycle1, cycle2])
# plt.show()


# Example usage:
# TSdiagram('Water', extracted_ts=[(300, 500), (350, 600), (400, 700)])
