"""analysis.py - post-study analysis: accuracy, t-test, effect size, plots."""
import sqlite3

import pandas as pd


def _conn():
    return sqlite3.connect("study.db")


def load_dataframe() -> pd.DataFrame:
    c = _conn()
    df = pd.read_sql_query("""
        SELECT p.pid, p.group_name, s.phase, s.problem, s.student_answer,
               s.correct, s.misconception, s.seconds
        FROM sessions s JOIN participants p ON s.pid = p.pid
    """, c)
    c.close()
    return df


def phase_scores(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (pid, phase) with accuracy."""
    g = df.groupby(["pid", "group_name", "phase"])["correct"].agg(["sum", "count"])
    g["accuracy"] = g["sum"] / g["count"]
    return g.reset_index()


def group_means(df: pd.DataFrame) -> pd.DataFrame:
    """Mean accuracy per group per phase."""
    p = phase_scores(df)
    return p.groupby(["group_name", "phase"])["accuracy"].agg(["mean", "std", "count"])


def repeated_misconceptions(df: pd.DataFrame) -> pd.DataFrame:
    """For each pid, count how many times the same misconception recurs."""
    learning = df[df["phase"] == "learning"]
    g = learning.groupby(["pid", "group_name", "misconception"]).size().reset_index(name="repeats")
    return g[g["misconception"] != ""]


def run_stats(df: pd.DataFrame) -> dict:
    """Paired t-test within groups, independent t-test between groups."""
    from scipy import stats
    p = phase_scores(df)
    out = {}

    # Within-group: pre vs post
    for group in p["group_name"].unique():
        pre = p[(p["group_name"] == group) & (p["phase"] == "pretest")].set_index("pid")["accuracy"]
        post = p[(p["group_name"] == group) & (p["phase"] == "posttest")].set_index("pid")["accuracy"]
        common = pre.index.intersection(post.index)
        if len(common) >= 3:
            t, pval = stats.ttest_rel(post.loc[common], pre.loc[common])
            d = (post.loc[common].mean() - pre.loc[common].mean()) / post.loc[common].std()
            out[f"{group}_pre_vs_post"] = {"t": t, "p": pval, "cohens_d": d, "n": len(common)}

    # Between-group: post-test comparison
    post_all = p[p["phase"] == "posttest"]
    groups = post_all["group_name"].unique()
    if len(groups) == 2:
        a = post_all[post_all["group_name"] == groups[0]]["accuracy"]
        b = post_all[post_all["group_name"] == groups[1]]["accuracy"]
        t, pval = stats.ttest_ind(a, b)
        d = (a.mean() - b.mean()) / ((a.std() + b.std()) / 2)
        out["between_post"] = {"t": t, "p": pval, "cohens_d": d,
                                "n_a": len(a), "n_b": len(b),
                                "group_a": groups[0], "group_b": groups[1]}
    return out


if __name__ == "__main__":
    df = load_dataframe()
    if df.empty:
        print("No study data yet.")
    else:
        print("Group means:")
        print(group_means(df))
        print()
        print("Repeated misconceptions per participant:")
        print(repeated_misconceptions(df).head(20))
        print()
        print("Statistics:")
        for k, v in run_stats(df).items():
            print(f"  {k}: {v}")