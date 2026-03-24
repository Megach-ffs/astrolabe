"""
Chart builder utility functions.

Pure functions that create matplotlib or Plotly figures.
No Streamlit imports — all rendering logic is separated for testability.
"""

import matplotlib.pyplot as plt
import matplotlib

# Use non-interactive backend for safety
matplotlib.use("Agg")

# Dark theme settings for all matplotlib charts
DARK_BG = "#0E1117"
DARK_FG = "#FAFAFA"
DARK_GRID = "#333333"
COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
    "#FFA15A", "#19D3F3", "#FF6692", "#B6E880",
    "#FF97FF", "#FECB52",
]


def _apply_dark_theme(fig, ax):
    """Apply dark theme to a matplotlib figure."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(DARK_BG)
    ax.tick_params(colors=DARK_FG)
    ax.xaxis.label.set_color(DARK_FG)
    ax.yaxis.label.set_color(DARK_FG)
    ax.title.set_color(DARK_FG)
    for spine in ax.spines.values():
        spine.set_color(DARK_GRID)


# ──────────────────────────────────────────────
# Filtering Helper
# ──────────────────────────────────────────────

def filter_dataframe(df, filters):
    """
    Filter a DataFrame based on a dict of filters.

    Args:
        df: Input DataFrame.
        filters: Dict where key is column name and value is:
            - list: keep only rows where column value is in the list
            - tuple of (min, max): keep rows in range (numeric)

    Returns:
        Filtered DataFrame.
    """
    result = df.copy()
    for col, condition in filters.items():
        if col not in result.columns:
            continue
        if isinstance(condition, (list, set)):
            result = result[result[col].isin(condition)]
        elif isinstance(condition, tuple) and len(condition) == 2:
            lo, hi = condition
            result = result[
                (result[col] >= lo) & (result[col] <= hi)
            ]
    return result


# ──────────────────────────────────────────────
# Matplotlib Chart Builders
# ──────────────────────────────────────────────

def build_histogram(df, column, bins=30, color_col=None):
    """
    Build a histogram.

    Args:
        df: Input DataFrame.
        column: Column to plot.
        bins: Number of bins.
        color_col: Optional column for grouped histograms.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_theme(fig, ax)

    if color_col and color_col in df.columns:
        groups = df[color_col].dropna().unique()
        for i, group in enumerate(groups):
            subset = df[df[color_col] == group][column].dropna()
            ax.hist(subset, bins=bins, alpha=0.6,
                    label=str(group), color=COLORS[i % len(COLORS)])
        ax.legend(facecolor=DARK_BG, edgecolor=DARK_GRID,
                  labelcolor=DARK_FG)
    else:
        ax.hist(df[column].dropna(), bins=bins, color=COLORS[0],
                edgecolor="white", linewidth=0.5)

    ax.set_xlabel(column)
    ax.set_ylabel("Count")
    ax.set_title(f"Histogram of {column}")
    fig.tight_layout()
    return fig


def build_box_plot(df, column, group_col=None):
    """
    Build a box plot.

    Args:
        column: Numeric column.
        group_col: Optional categorical column for grouped boxes.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_theme(fig, ax)

    if group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique()
        data = [df[df[group_col] == g][column].dropna() for g in groups]
        bp = ax.boxplot(data, labels=[str(g) for g in groups],
                        patch_artist=True)
        for i, patch in enumerate(bp["boxes"]):
            patch.set_facecolor(COLORS[i % len(COLORS)])
            patch.set_alpha(0.7)
        for element in ["whiskers", "caps", "medians"]:
            for item in bp[element]:
                item.set_color(DARK_FG)
        for flier in bp["fliers"]:
            flier.set_markeredgecolor(DARK_FG)
    else:
        bp = ax.boxplot(df[column].dropna(), patch_artist=True)
        bp["boxes"][0].set_facecolor(COLORS[0])
        bp["boxes"][0].set_alpha(0.7)
        for element in ["whiskers", "caps", "medians"]:
            for item in bp[element]:
                item.set_color(DARK_FG)

    ax.set_ylabel(column)
    title = f"Box Plot of {column}"
    if group_col:
        title += f" by {group_col}"
    ax.set_title(title)
    fig.tight_layout()
    return fig


def build_scatter(df, x_col, y_col, color_col=None):
    """
    Build a scatter plot.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(fig, ax)

    if color_col and color_col in df.columns:
        groups = df[color_col].dropna().unique()
        for i, group in enumerate(groups):
            subset = df[df[color_col] == group]
            ax.scatter(subset[x_col], subset[y_col], alpha=0.6,
                       label=str(group), color=COLORS[i % len(COLORS)], s=30)
        ax.legend(facecolor=DARK_BG, edgecolor=DARK_GRID,
                  labelcolor=DARK_FG)
    else:
        ax.scatter(df[x_col], df[y_col], alpha=0.6,
                   color=COLORS[0], s=30)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} vs {x_col}")
    fig.tight_layout()
    return fig


def build_line_chart(df, x_col, y_col, color_col=None):
    """
    Build a line chart (time series style).

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    _apply_dark_theme(fig, ax)

    plot_df = df.sort_values(x_col)

    if color_col and color_col in df.columns:
        groups = plot_df[color_col].dropna().unique()
        for i, group in enumerate(groups):
            subset = plot_df[plot_df[color_col] == group]
            ax.plot(subset[x_col], subset[y_col], label=str(group),
                    color=COLORS[i % len(COLORS)], linewidth=1.5)
        ax.legend(facecolor=DARK_BG, edgecolor=DARK_GRID,
                  labelcolor=DARK_FG)
    else:
        ax.plot(plot_df[x_col], plot_df[y_col],
                color=COLORS[0], linewidth=1.5)

    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    ax.set_title(f"{y_col} over {x_col}")
    plt.xticks(rotation=45)
    fig.tight_layout()
    return fig


def build_bar_chart(df, x_col, y_col, agg="mean", color_col=None,
                    top_n=None):
    """
    Build a grouped/aggregated bar chart.

    Args:
        agg: One of 'sum', 'mean', 'count', 'median'.
        top_n: If set, show only top N categories by the aggregated value.

    Returns:
        matplotlib Figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(fig, ax)

    if color_col and color_col in df.columns:
        grouped = df.groupby([x_col, color_col])[y_col].agg(agg).unstack()
        if top_n:
            row_totals = grouped.sum(axis=1).nlargest(top_n)
            grouped = grouped.loc[row_totals.index]
        grouped.plot(kind="bar", ax=ax, color=COLORS[:len(grouped.columns)],
                     edgecolor="white", linewidth=0.5)
        ax.legend(facecolor=DARK_BG, edgecolor=DARK_GRID,
                  labelcolor=DARK_FG)
    else:
        if agg == "count":
            agg_data = df.groupby(x_col)[y_col].count()
        else:
            agg_data = df.groupby(x_col)[y_col].agg(agg)

        if top_n:
            agg_data = agg_data.nlargest(top_n)

        agg_data.plot(kind="bar", ax=ax, color=COLORS[0],
                      edgecolor="white", linewidth=0.5)

    ax.set_xlabel(x_col)
    ax.set_ylabel(f"{agg}({y_col})")
    ax.set_title(f"{agg.title()} of {y_col} by {x_col}")
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    return fig


def build_heatmap(df, columns=None):
    """
    Build a correlation heatmap for numeric columns.

    Args:
        columns: List of numeric columns. If None, uses all numeric.

    Returns:
        matplotlib Figure.
    """
    if columns:
        numeric_df = df[columns].select_dtypes(include="number")
    else:
        numeric_df = df.select_dtypes(include="number")

    corr = numeric_df.corr()

    fig, ax = plt.subplots(figsize=(max(8, len(corr) * 0.8),
                                    max(6, len(corr) * 0.6)))
    _apply_dark_theme(fig, ax)

    im = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.tick_params(colors=DARK_FG)
    cbar.outline.set_edgecolor(DARK_GRID)

    cols = corr.columns.tolist()
    ax.set_xticks(range(len(cols)))
    ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticklabels(cols)

    # Add correlation values
    for i in range(len(cols)):
        for j in range(len(cols)):
            val = corr.iloc[i, j]
            text_color = "white" if abs(val) > 0.5 else DARK_FG
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color=text_color, fontsize=9)

    ax.set_title("Correlation Matrix")
    fig.tight_layout()
    return fig


# ──────────────────────────────────────────────
# Plotly Chart Builders (optional bonus)
# ──────────────────────────────────────────────

def _get_plotly():
    """Lazy import plotly — returns (px, go) or raises ImportError."""
    import plotly.express as px
    import plotly.graph_objects as go
    return px, go


def build_histogram_plotly(df, column, bins=30, color_col=None):
    """Build a Plotly histogram."""
    px, _ = _get_plotly()
    fig = px.histogram(
        df, x=column, color=color_col, nbins=bins,
        template="plotly_dark",
        title=f"Histogram of {column}",
    )
    return fig


def build_box_plot_plotly(df, column, group_col=None):
    """Build a Plotly box plot."""
    px, _ = _get_plotly()
    fig = px.box(
        df, y=column, x=group_col, color=group_col,
        template="plotly_dark",
        title=f"Box Plot of {column}",
    )
    return fig


def build_scatter_plotly(df, x_col, y_col, color_col=None):
    """Build a Plotly scatter plot."""
    px, _ = _get_plotly()
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        template="plotly_dark",
        title=f"{y_col} vs {x_col}",
    )
    return fig


def build_line_chart_plotly(df, x_col, y_col, color_col=None):
    """Build a Plotly line chart."""
    px, _ = _get_plotly()
    plot_df = df.sort_values(x_col)
    fig = px.line(
        plot_df, x=x_col, y=y_col, color=color_col,
        template="plotly_dark",
        title=f"{y_col} over {x_col}",
    )
    return fig


def build_bar_chart_plotly(df, x_col, y_col, agg="mean", color_col=None,
                           top_n=None):
    """Build a Plotly bar chart."""
    px, _ = _get_plotly()

    if color_col:
        grouped = df.groupby([x_col, color_col])[y_col].agg(agg).reset_index()
    else:
        if agg == "count":
            grouped = df.groupby(x_col)[y_col].count().reset_index()
        else:
            grouped = df.groupby(x_col)[y_col].agg(agg).reset_index()

    if top_n:
        top_cats = (
            grouped.groupby(x_col)[y_col].sum()
            .nlargest(top_n).index
        )
        grouped = grouped[grouped[x_col].isin(top_cats)]

    fig = px.bar(
        grouped, x=x_col, y=y_col, color=color_col,
        template="plotly_dark",
        title=f"{agg.title()} of {y_col} by {x_col}",
    )
    return fig


def build_heatmap_plotly(df, columns=None):
    """Build a Plotly correlation heatmap."""
    _, go = _get_plotly()
    import plotly.express as px

    if columns:
        numeric_df = df[columns].select_dtypes(include="number")
    else:
        numeric_df = df.select_dtypes(include="number")

    corr = numeric_df.corr()

    fig = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1, template="plotly_dark",
        title="Correlation Matrix",
    )
    return fig


# ──────────────────────────────────────────────
# PNG Export Helper
# ──────────────────────────────────────────────

def fig_to_png_bytes(fig):
    """Convert a matplotlib Figure to PNG bytes for download."""
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    buf.seek(0)
    return buf.getvalue()
