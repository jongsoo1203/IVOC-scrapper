# scraper_app/tools/dedupe.py
import pandas as pd


def _norm(x) -> str:
    if pd.isna(x):
        return ""
    return " ".join(str(x).strip().lower().split())


def remove_duplicates_df(
    df: pd.DataFrame,
    *,
    title_col: int = 2,
    desc_col: int = 3,
    link_col: int = 4,
    comments_col: int = 5,
    short_title_max_len: int = 35,
    long_title_min_len: int = 70,
) -> pd.DataFrame:
    """
    Dedupe rules (based on your spec):

    i) If link matches -> remove duplicates (keep first)
    ii) If description matches:
        - if link also matches -> remove
        - else if comments exist -> keep
        - else remove
    iii) If title matches and NO comments -> remove,
         BUT keep common short titles; remove long repeated titles.
    """

    if df is None or df.empty:
        return df

    # Ensure enough columns exist
    for col in [title_col, desc_col, link_col, comments_col]:
        if col >= df.shape[1]:
            # If comments column doesn't exist, create it
            while df.shape[1] <= col:
                df[df.shape[1]] = ""

    df = df.copy()

    # Normalized fields
    df["_title"] = df[title_col].apply(_norm)
    df["_desc"] = df[desc_col].apply(_norm)
    df["_link"] = df[link_col].apply(_norm)
    df["_comments"] = df[comments_col].apply(_norm)
    df["_has_comments"] = df["_comments"].apply(lambda s: len(s) > 0 and s not in ("[]", "nan"))

    keep = [True] * len(df)

    seen_link = {}
    seen_desc = {}   # desc -> list of indices kept (for comparisons)
    seen_title = {}  # title -> list of indices kept

    for i, row in df.iterrows():
        link = row["_link"]
        desc = row["_desc"]
        title = row["_title"]
        has_comments = bool(row["_has_comments"])

        # ---- i) link match => drop duplicates
        if link:
            if link in seen_link:
                keep[i] = False
                continue
            seen_link[link] = i

        # ---- ii) description match logic
        if desc:
            if desc in seen_desc:
                # Compare against first kept row with same desc
                # If any kept row has same desc and same link => remove
                remove_due_desc = False
                for j in seen_desc[desc]:
                    if not keep[j]:
                        continue
                    if df.loc[j, "_link"] == link and link:
                        remove_due_desc = True
                        break

                if remove_due_desc:
                    keep[i] = False
                    continue

                # If link differs, keep only if comments exist
                if not has_comments:
                    keep[i] = False
                    continue

            # record desc seen (only if still kept)
            seen_desc.setdefault(desc, []).append(i)

        # ---- iii) title match logic (only if no comments)
        if title and not has_comments:
            if title in seen_title:
                # keep common short titles, remove long repeated titles
                tlen = len(title)
                if tlen >= long_title_min_len:
                    keep[i] = False
                    continue
                # if short, keep
            seen_title.setdefault(title, []).append(i)
        else:
            if title:
                seen_title.setdefault(title, []).append(i)

    out = df.loc[keep].drop(columns=["_title", "_desc", "_link", "_comments", "_has_comments"])
    out = out.reset_index(drop=True)
    return out
