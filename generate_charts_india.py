import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "sans-serif", "font.size": 11,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#0b0b0b", "text.color": "#0b0b0b",
    "xtick.color": "#52514e", "ytick.color": "#52514e",
    "figure.facecolor": "white", "axes.facecolor": "white",
})

GREEN = "#0F6E56"; AMBER = "#854F0B"; RED = "#791F1F"; ACCENT = "#185FA5"; GREY = "#898781"

results = pd.read_csv("benchmark_results_india.csv")
curves = np.load("best_model_curves_india.npz", allow_pickle=True)

# 1. Model comparison (top-20% capture rate -- the metric we actually selected on)
fig, ax = plt.subplots(figsize=(7.5, 4))
results_sorted = results.sort_values("top20_capture_rate", ascending=False).reset_index(drop=True)
labels = [f"{r.model.replace('_',' ').title()}\n({r.feature_set.replace('_',' ')})" for r in results_sorted.itertuples()]
colors = [ACCENT if fs == "core_fields" else GREEN for fs in results_sorted["feature_set"]]
bars = ax.bar(labels, results_sorted["top20_capture_rate"] * 100, color=colors)
ax.set_ylim(70, 92)
ax.set_ylabel("Top-20% capture rate (%)")
ax.set_title("Model comparison: 3 models x 2 feature sets", fontsize=13, fontweight="bold")
for b, v in zip(bars, results_sorted["top20_capture_rate"] * 100):
    ax.text(b.get_x() + b.get_width()/2, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9)
handles = [plt.Rectangle((0,0),1,1, color=ACCENT), plt.Rectangle((0,0),1,1, color=GREEN)]
ax.legend(handles, ["Core fields (19)", "Full fields (143)"], loc="lower right", frameon=False, fontsize=9)
plt.xticks(rotation=15, ha="right", fontsize=9)
plt.tight_layout()
plt.savefig("charts/india_01_model_comparison.png", dpi=160)
plt.close()

# 2. ROC curve
fig, ax = plt.subplots(figsize=(5.5, 5))
ax.plot(curves["fpr"], curves["tpr"], color=ACCENT, linewidth=2,
        label=f"{str(curves['best_model']).replace('_',' ').title()} ({str(curves['best_feature_set']).replace('_',' ')})")
ax.plot([0,1],[0,1], color=GREY, linestyle="--", linewidth=1, label="Random")
ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
ax.set_title("ROC curve, selected configuration", fontsize=13, fontweight="bold")
ax.legend(loc="lower right", frameon=False, fontsize=9)
plt.tight_layout()
plt.savefig("charts/india_02_roc_curve.png", dpi=160)
plt.close()

# 3. Precision-Recall curve (more informative than ROC under 8.6% class imbalance)
fig, ax = plt.subplots(figsize=(5.5, 5))
ax.plot(curves["rec_curve"], curves["prec_curve"], color=RED, linewidth=2, label="Model")
base_rate = curves["y_test"].mean()
ax.axhline(base_rate, color=GREY, linestyle="--", linewidth=1, label=f"Random ({base_rate*100:.1f}% churn rate)")
ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
ax.set_title("Precision-recall curve, selected configuration", fontsize=13, fontweight="bold")
ax.legend(loc="upper right", frameon=False, fontsize=9)
plt.tight_layout()
plt.savefig("charts/india_03_pr_curve.png", dpi=160)
plt.close()

# 4. Confusion matrix
cm = curves["cm"]
fig, ax = plt.subplots(figsize=(4.5, 4))
im = ax.imshow(cm, cmap="Greens")
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                color="white" if cm[i,j] > cm.max()/2 else "black", fontsize=14, fontweight="bold")
ax.set_xticks([0,1]); ax.set_xticklabels(["Predicted: stay", "Predicted: churn"], fontsize=9)
ax.set_yticks([0,1]); ax.set_yticklabels(["Actual: stay", "Actual: churn"], fontsize=9)
ax.set_title("Confusion matrix, selected configuration", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("charts/india_04_confusion_matrix.png", dpi=160)
plt.close()

# 5. Feature importance, top 15
fi = pd.read_csv("feature_importance_india.csv", index_col=0).iloc[:, 0]
fig, ax = plt.subplots(figsize=(7.5, 5))
fi_sorted = fi.sort_values()
ax.barh(fi_sorted.index, fi_sorted.values, color=GREEN)
ax.set_title("Feature importance, top 15, selected configuration", fontsize=13, fontweight="bold")
ax.set_xlabel("Importance")
plt.tight_layout()
plt.savefig("charts/india_05_feature_importance.png", dpi=160)
plt.close()

# 6. Lift / gains
y_test = curves["y_test"]; proba = curves["proba"]
order = np.argsort(-proba)
y_sorted = y_test[order]
cum_churn = np.cumsum(y_sorted) / y_sorted.sum()
pct_contacted = np.arange(1, len(y_sorted)+1) / len(y_sorted)

fig, ax = plt.subplots(figsize=(6, 5))
ax.plot(pct_contacted*100, cum_churn*100, color=ACCENT, linewidth=2, label="Model-ranked outreach")
ax.plot([0,100],[0,100], color=GREY, linestyle="--", linewidth=1, label="Random outreach")
ax.axvline(20, color=RED, linestyle=":", linewidth=1)
capture_at_20 = cum_churn[int(len(cum_churn)*0.20)] * 100
ax.scatter([20],[capture_at_20], color=RED, zorder=5)
ax.annotate(f"Top 20% called\ncatches {capture_at_20:.0f}% of churners",
            xy=(20, capture_at_20), xytext=(32, capture_at_20-22),
            fontsize=9, color=RED, arrowprops=dict(arrowstyle="->", color=RED, lw=1))
ax.set_xlabel("% of high-value customers contacted (ranked by risk score)")
ax.set_ylabel("% of actual churners captured")
ax.set_title("Lift / gains: who to call first", fontsize=13, fontweight="bold")
ax.legend(loc="lower right", frameon=False, fontsize=9)
plt.tight_layout()
plt.savefig("charts/india_06_lift_gains.png", dpi=160)
plt.close()

print("Charts written to charts/india_*.png")
